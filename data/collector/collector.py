import requests
import time
import hashlib
import os
from dotenv import load_dotenv
from data.database.db import get_connection

BASE_URL = "https://api.brawlstars.com/v1"

def gerar_match_hash(battle_time, lista_tags):
    """Gera um ID único e determinístico para a partida."""
    tags_ordenadas = sorted(lista_tags)
    string_base = battle_time + "".join(tags_ordenadas)
    return hashlib.sha256(string_base.encode('utf-8')).hexdigest()

def executar_coleta():
    """Função principal que orquestra a coleta de dados da API."""
    
    # 1. Carregamento de credenciais (Isolado na função)
    load_dotenv()
    TOKEN = os.getenv("BRAWL_API_TOKEN")
    if not TOKEN:
        print("Erro Crítico: BRAWL_API_TOKEN não encontrado.")
        return
        
    HEADERS = {"Authorization": f"Bearer {TOKEN}"}
    alvos = ["#8QV90CYQ", "#8JJG8L8J9", "#90CV29899"]

    # 2. Setup do Banco de Dados (Isolado na função)
    conn = get_connection()
    cur = conn.cursor()

    query_inserir_partida = """
        INSERT OR IGNORE INTO matches (match_hash, battle_time, mode, map, duration)
        VALUES (?, ?, ?, ?, ?)
    """
    query_inserir_jogador = """
        INSERT OR IGNORE INTO players (tag, name)
        VALUES (?, ?)
    """
    query_inserir_relacao = """
        INSERT OR IGNORE INTO match_players 
        (match_hash, player_tag, team_id, brawler_name, power, trophies, result)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    # 3. Motor de Coleta
    for tag_alvo in alvos:
        tag_formatada = tag_alvo.replace("#", "%23")
        url = f"{BASE_URL}/players/{tag_formatada}/battlelog"
        
        resposta = requests.get(url, headers=HEADERS)
        
        if resposta.status_code != 200:
            print(f"Erro ao buscar dados de {tag_alvo}: Código {resposta.status_code}")
            continue
            
        battlelog = resposta.json().get("items", [])
        
        for item in battlelog:
            battle = item.get("battle", {})
            
            if "teams" not in battle:
                continue
                
            battle_time = item.get("battleTime")
            mode = battle.get("mode")
            map_name = item.get("event", {}).get("map")
            duration = battle.get("duration", 0)
            
            todas_tags_partida = []
            for team in battle["teams"]:
                for player in team:
                    todas_tags_partida.append(player["tag"])
                    
            match_hash = gerar_match_hash(battle_time, todas_tags_partida)
            
            cur.execute(query_inserir_partida, (match_hash, battle_time, mode, map_name, duration))
            
            resultado_alvo = battle.get("result", "unknown")

            # Identifica o time do jogador alvo
            team_do_alvo = None
            for tid, team in enumerate(battle["teams"]):
                if any(p["tag"] == tag_alvo for p in team):
                    team_do_alvo = tid
                    break

            # Processa e insere os jogadores
            for team_id, team in enumerate(battle["teams"]):
                if team_id == team_do_alvo:
                    resultado_time = resultado_alvo
                else:
                    if resultado_alvo == "victory":
                        resultado_time = "defeat"
                    elif resultado_alvo == "defeat":
                        resultado_time = "victory"
                    else:
                        resultado_time = resultado_alvo
                
                for player in team:
                    player_tag = player.get("tag")
                    
                    cur.execute(query_inserir_jogador, (player_tag, player.get("name")))
                    
                    brawler = player.get("brawler", {})
                    dados_relacao = (
                        match_hash, player_tag, team_id, 
                        brawler.get("name"), brawler.get("power"), 
                        brawler.get("trophies"), resultado_time
                    )
                    cur.execute(query_inserir_relacao, dados_relacao)
                    
        # Confirma a transação após processar todas as partidas deste alvo
        conn.commit()
        time.sleep(1)
        
    cur.execute("SELECT COUNT(*) FROM match_players")    
    print("Total de registros em match_players:", cur.fetchone()[0])
    
    # 4. Encerramento seguro da conexão
    conn.close()