import requests
import time
import hashlib
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from data.database.db import get_connection

BASE_URL = "https://api.brawlstars.com/v1"

def generate_match_hash(battle_time, tag_list):
    """Generates a unique and deterministic ID for the match."""
    sorted_tags = sorted(tag_list)
    base_string = battle_time + "".join(sorted_tags)
    return hashlib.sha256(base_string.encode('utf-8')).hexdigest()

def inject_fresh_blood(cur, conn, headers):
    """Busca os top jogadores globais para quebrar a bolha de matchmaking."""
    print("\n[Injeção Automática] Buscando novos jogadores fora da bolha atual...")
    url = f"{BASE_URL}/rankings/global/players?limit=50"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        players = response.json().get("items", [])
        for p in players:
            # Insere novos jogadores. Se já existirem, o IGNORE ignora.
            # last_scanned como NULL garante que eles irão para o topo da fila.
            cur.execute(
                "INSERT OR IGNORE INTO players (tag, name, last_scanned) VALUES (?, ?, NULL)",
                (p.get("tag"), p.get("name"))
            )
        conn.commit()
        print(f"[Injeção Automática] Até {len(players)} novos jogadores de elite adicionados à fila.\n")
    elif response.status_code == 429:
        print("[Injeção Automática] Rate limit atingido. Tentaremos injetar depois.\n")

def run_collector():
    """Main function that orchestrates data collection from the API as a Crawler."""
    load_dotenv()
    TOKEN = os.getenv("BRAWL_API_TOKEN")
    if not TOKEN:
        print("Critical Error: BRAWL_API_TOKEN not found in the .env file.")
        return
        
    HEADERS = {"Authorization": f"Bearer {TOKEN}"}

    conn = get_connection()
    cur = conn.cursor()

    query_insert_match = """
        INSERT OR IGNORE INTO matches (match_hash, battle_time, mode, map, duration)
        VALUES (?, ?, ?, ?, ?)
    """
    
    # New Player goes in with NULL timestamp (meaning pending/never scanned)
    query_insert_player = """
        INSERT OR IGNORE INTO players (tag, name, last_scanned)
        VALUES (?, ?, NULL)
    """
    
    query_insert_relation = """
        INSERT OR IGNORE INTO match_players 
        (match_hash, player_tag, team_id, brawler_name, power, trophies, result)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    # 1. Inject initial seeds
    cur.execute("SELECT COUNT(*) FROM players")
    if cur.fetchone()[0] == 0:
        print("Database empty. Discovering elite seeds to start...")
        seeds = get_seed_players(HEADERS)
        for seed in seeds:
            cur.execute("INSERT OR IGNORE INTO players (tag, name, last_scanned) VALUES (?, ?, NULL)", 
                        (seed, "Elite Seed"))
        conn.commit()

    BATCH_LIMIT = 500
    processed_targets = 0

    print(f"Crawler Engine started. Limit set to {BATCH_LIMIT} targets.")

    # Calculate the exact timestamp for 20 days ago (Cooldown window)
    cooldown_limit = (datetime.utcnow() - timedelta(days=20)).strftime('%Y-%m-%d %H:%M:%S')

    try:
        while processed_targets < BATCH_LIMIT:
            if processed_targets > 0 and processed_targets % 50 == 0:
                inject_fresh_blood(cur, conn, HEADERS)
            
            # Polling mechanism: Fetch players never scanned OR scanned more than 20 days ago
            fetch_query = """
                SELECT tag FROM players 
                WHERE last_scanned IS NULL OR last_scanned <= ? 
                LIMIT 1
            """
            cur.execute(fetch_query, (cooldown_limit,))
            result = cur.fetchone()
            
            if not result:
                print("Processing queue is empty or all players are currently on a 20-day cooldown.")
                break
                
            target_tag = result[0]
            print(f"[{time.strftime('%H:%M:%S')}] Processing target: {target_tag}")
            
            formatted_tag = target_tag.replace("#", "%23")
            url = f"{BASE_URL}/players/{formatted_tag}/battlelog"
            
            response = requests.get(url, headers=HEADERS)
            
            if response.status_code == 200:
                battlelog = response.json().get("items", [])
                
                # VARIANCE BARRIER 2.0: Tracks (Map, Brawler) combinations
                
                for item in battlelog:
                    battle = item.get("battle", {})
                    
                    if "teams" not in battle:
                        continue
                        
                    map_name = item.get("event", {}).get("map")
                    if not map_name:
                        continue
                        
                    # Pre-scan the teams to find which Brawler the target player used
                    target_brawler = None
                    for team in battle["teams"]:
                        for p in team:
                            if p["tag"] == target_tag:
                                target_brawler = p.get("brawler", {}).get("name")
                                break
                        if target_brawler:
                            break
                            
                    if not target_brawler:
                        continue
                    
                    battle_time = item.get("battleTime")
                    mode = battle.get("mode")
                    duration = battle.get("duration", 0)
                    
                    all_match_tags = []
                    target_team_index = None
                    target_result = battle.get("result", "unknown")
                    
                    for tid, team in enumerate(battle["teams"]):
                        for player in team:
                            all_match_tags.append(player["tag"])
                            if player["tag"] == target_tag:
                                target_team_index = tid

                    if target_team_index is None:
                        continue
                        
                    match_hash = generate_match_hash(battle_time, all_match_tags)
                    cur.execute(query_insert_match, (match_hash, battle_time, mode, map_name, duration))

                    for team_id, team in enumerate(battle["teams"]):
                        if team_id == target_team_index:
                            team_result = target_result
                        else:
                            if target_result == "victory":
                                team_result = "defeat"
                            elif target_result == "defeat":
                                team_result = "victory"
                            else:
                                team_result = target_result
                        
                        for player in team:
                            player_tag = player.get("tag")
                            
                            # Insert new player discovered into the ecosystem
                            cur.execute(query_insert_player, (player_tag, player.get("name")))
                            
                            brawler = player.get("brawler", {})
                            relation_data = (
                                match_hash, player_tag, team_id, 
                                brawler.get("name"), brawler.get("power"), 
                                brawler.get("trophies"), team_result
                            )
                            cur.execute(query_insert_relation, relation_data)
                            
            elif response.status_code == 429:
                print("API rate limit exceeded. Pausing for 10 seconds.")
                time.sleep(10)
                continue
                
            # Update the player's last_scanned timestamp to CURRENT UTC time, triggering the 20-day cooldown
            cur.execute("UPDATE players SET last_scanned = datetime('now') WHERE tag = ?", (target_tag,))
            conn.commit()
            
            processed_targets += 1
            print(f"Progress: {processed_targets}/{BATCH_LIMIT} processed.\n")
            time.sleep(0.6)

        print(f"Batch of {BATCH_LIMIT} processed successfully. Safety stop.")

    except KeyboardInterrupt:
        print("\n[Warning] Manual interruption detected from user.")
        conn.commit()

    finally:
        cur.execute("SELECT COUNT(*) FROM match_players")    
        print("Total records in match_players table:", cur.fetchone()[0])
        conn.close()
        
def get_all_brawler_ids(headers):
    """Fetches all valid Brawler IDs from the API."""
    url = f"{BASE_URL}/brawlers"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return [b['id'] for b in response.json()['items']]
    return []
        
def get_seed_players(headers):
    """Fetches the #1 player for every brawler to seed the Crawler."""
    # List of all brawler IDs (You can get these from the /brawlers endpoint)
    # This is a sample, ensure you have the correct brawler IDs
    brawler_ids = [16000000, 16000001, ...] # Exemplo de IDs
    seeds = set()

    for b_id in brawler_ids:
        url = f"{BASE_URL}/rankings/global/brawlers/{b_id}?limit=1"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            rankings = response.json().get("items", [])
            for item in rankings:
                tag = item.get("tag")
                if tag:
                    seeds.add(tag)
        time.sleep(0.5)  # To avoid hitting rate limits    
        
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 10))
            print(f"Rate limit hit. Waiting {retry_after} seconds.")
            time.sleep(retry_after)
            continue      
              
    return seeds