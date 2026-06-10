
from dotenv import load_dotenv
from data.database.db import get_connection, initdb
import requests
import time
import hashlib
import os

BASE_URL = "https://api.brawlstars.com/v1"

load_dotenv()
TOKEN = os.getenv("BRAWL_API_TOKEN")
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
alvos = ["#8QV90CYQ", "#8JJG8L8J9", "#90CV29899"]


# GERAÇÃO DO MATCH HASH
def gerar_match_hash(battle_time, lista_tags):
    """
    Gera um ID único e determinístico para a partida.
    Ordena as tags para que a ordem dos jogadores não altere o resultado.
    """
    tags_ordenadas = sorted(lista_tags)
    string_base = battle_time + "".join(tags_ordenadas)
    
    # Cria um hash criptográfico (SHA-256) da string combinada
    return hashlib.sha256(string_base.encode('utf-8')).hexdigest()


# SETUP DO BANCO DE DADOS
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


# COLETA E PROCESSAMENTO DAS PARTIDAS
for tag_alvo in alvos:
    
    tag_formatada = tag_alvo.replace("#", "%23")
    url = f"https://api.brawlstars.com/v1/players/{tag_formatada}/battlelog"
    
    resposta = requests.get(url, headers=HEADERS)
    
    if resposta.status_code != 200:
        print(f"Erro ao buscar dados de {tag_alvo}: Código {resposta.status_code}")
        continue
        
    battlelog = resposta.json().get("items", [])
    
    for item in battlelog:
        battle = item.get("battle", {})
        
        # Filtra apenas partidas de modo 3v3 (que possuem 'teams')
        if "teams" not in battle:
            continue
            
        battle_time = item.get("battleTime")
        mode = battle.get("mode")
        map_name = item.get("event", {}).get("map")
        duration = battle.get("duration", 0)
        
        # Extrai todas as tags da partida para gerar o Hash Único
        todas_tags_partida = []
        for team in battle["teams"]:
            for player in team:
                todas_tags_partida.append(player["tag"])
                
        match_hash = gerar_match_hash(battle_time, todas_tags_partida)
        
        # insere a partida (ignora se já existir)
        dados_partida = (match_hash, battle_time, mode, map_name, duration)
        cur.execute(query_inserir_partida, dados_partida)
        
        # processa as equipes, os jogadores e os resultados
        for team_id, team in enumerate(battle["teams"]):
            # Lógica para definir quem ganhou. 
            # A API geralmente marca o resultado do ponto de vista do jogador alvo
            resultado_time = battle.get("result", "unknown") 
            
            for player in team:
                player_tag = player.get("tag")
                player_name = player.get("name")
                brawler = player.get("brawler", {})
                brawler_name = brawler.get("name")
                power = brawler.get("power")
                trophies = brawler.get("trophies")
                
                # insere o jogador
                dados_jogador = (player_tag, player_name)
                cur.execute(query_inserir_jogador, dados_jogador)
                
                # insere a relação de performance
                dados_relacao = (
                    match_hash, player_tag, team_id, 
                    brawler_name, power, trophies, resultado_time
                )
                cur.execute(query_inserir_relacao, dados_relacao)
                
    # salva os dados processados para o jogador atual
    conn.commit()
    
    # pausa para respeitar o limite de chamadas da API
    time.sleep(1)

conn.close()
