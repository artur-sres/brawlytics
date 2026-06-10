import os
from dotenv import load_dotenv
import requests

load_dotenv()

BASE_URL = "https://api.brawlstars.com/v1"

TOKEN = os.getenv("BRAWL_API_TOKEN")
PLAYER_TAG = os.getenv("PLAYER_TAG")

# headers é necessário para autenticação na API do Brawl Stars, usando o token de acesso
headers = {
    "Authorization": f"Bearer {TOKEN}"
}
# faz uma solicitação GET para obter o log de batalhas de um jogador específico, usando o PLAYER_TAG e os headers para autenticação
def fetch_battlelog():
    url = f"{BASE_URL}/players/{PLAYER_TAG}/battlelog"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Erro na API:", response.status_code, response.text)
        return None

    return response.json()

# salva os dados de uma batalha específica no banco de dados, usando a conexão fornecida e os detalhes da batalha
def save_match(conn, battle):
    cur = conn.cursor()

    battle_time = battle["battleTime"]
    event = battle["event"]
    mode = event["mode"]
    map_name = event["map"]
    result = battle["battle"].get("result")
    duration = battle["battle"].get("duration")

    # inserir match
    query = """
        INSERT OR IGNORE INTO matches (battle_time, mode, map, duration, result)
        VALUES (?, ?, ?, ?, ?)
    """
    dados_partida = (battle_time, mode, map_name, duration, result)
    cur.execute(query, dados_partida)

    # pegar teams
    teams = battle["battle"].get("teams", [])
    for team_index, team in enumerate(teams):
        for player in team:
            brawler = player["brawler"]

            query = ("""
                INSERT INTO match_players (battle_time, team, brawler, power, trophies)
                VALUES (?, ?, ?, ?, ?)
            """)
            dados_jogador = (battle_time, team_index, brawler["name"], brawler["power"], player["trophies"])
            cur.execute(query, dados_jogador)

    # salvar as alterações no banco de dados 
    conn.commit()

