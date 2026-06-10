import os
from dotenv import load_dotenv
import requests

load_dotenv()

BASE_URL = "https://api.brawlstars.com/v1"

TOKEN = os.getenv("BRAWL_API_TOKEN")
PLAYER_TAG = os.getenv("PLAYER_TAG")

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

def fetch_battlelog():
    url = f"{BASE_URL}/players/{PLAYER_TAG}/battlelog"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Erro na API:", response.status_code, response.text)
        return None

    return response.json()

def save_match(conn, battle):
    cur = conn.cursor()

    battle_time = battle["battleTime"]
    event = battle["event"]
    mode = event["mode"]
    map_name = event["map"]

    result = battle["battle"].get("result")
    duration = battle["battle"].get("duration")

    # inserir match
    cur.execute("""
        INSERT OR IGNORE INTO matches (battle_time, mode, map, duration, result)
        VALUES (?, ?, ?, ?, ?)
    """, (battle_time, mode, map_name, duration, result))

    # pegar teams
    teams = battle["battle"].get("teams", [])

    for team_index, team in enumerate(teams):
        for player in team:
            brawler = player["brawler"]

            cur.execute("""
                INSERT INTO match_players (
                    battle_time, team, brawler, power, trophies
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                battle_time,
                team_index,
                brawler["name"],
                brawler.get("power"),
                brawler.get("trophies")
            ))

    conn.commit()

