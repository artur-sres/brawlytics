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
    """Função principal que orquestra a coleta de dados da API em formato Crawler."""
    load_dotenv()
    TOKEN = os.getenv("BRAWL_API_TOKEN")
    if not TOKEN:
        print("Erro Crítico: BRAWL_API_TOKEN não encontrado no ficheiro .env.")
        return
        
    HEADERS = {"Authorization": f"Bearer {TOKEN}"}

    conn = get_connection()
    cur = conn.cursor()

    query_inserir_partida = """
        INSERT OR IGNORE INTO matches (match_hash, battle_time, mode, map, duration)
        VALUES (?, ?, ?, ?, ?)
    """
    # Note o 'scanned = 0' que marca os novos jogadores como pendentes
    query_inserir_jogador = """
        INSERT OR IGNORE INTO players (tag, name, scanned)
        VALUES (?, ?, 0)
    """
    query_inserir_relacao = """
        INSERT OR IGNORE INTO match_players 
        (match_hash, player_tag, team_id, brawler_name, power, trophies, result)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    # 1. Injeta as sementes iniciais caso a base de dados esteja completamente vazia
    sementes = ["#8QV90CYQ", "#8JJG8L8J9", "#90CV29899"]
    for semente in sementes:
        cur.execute(query_inserir_jogador, (semente, "Desconhecido"))
    conn.commit()

    # 2. Configuração do Limite de Segurança
    LIMITE_POR_LOTE = 200
    alvos_processados = 0

    print(f"Motor Crawler iniciado. Limite configurado para {LIMITE_POR_LOTE} alvos.")

    # 3. Execução Controlada do Grafo (Crawler)
    try:
        while alvos_processados < LIMITE_POR_LOTE:
            # Busca estritamente 1 jogador que ainda não foi processado (scanned = 0)
            cur.execute("SELECT tag FROM players WHERE scanned = 0 LIMIT 1")
            resultado = cur.fetchone()
            
            if not resultado:
                print("Fila de processamento vazia. Todos os registos foram analisados.")
                break
                
            tag_alvo = resultado[0]
            print(f"[{time.strftime('%H:%M:%S')}] A processar alvo: {tag_alvo}")
            
            tag_formatada = tag_alvo.replace("#", "%23")
            url = f"{BASE_URL}/players/{tag_formatada}/battlelog"
            
            resposta = requests.get(url, headers=HEADERS)
            
            if resposta.status_code == 200:
                battlelog = resposta.json().get("items", [])
                
                # BARREIRA DE VARIÂNCIA: Rastreia os mapas já extraídos para ESTE jogador
                mapas_vistos = set()
                
                for item in battlelog:
                    battle = item.get("battle", {})
                    
                    # Filtra apenas partidas de modo 3v3 (que possuem 'teams')
                    if "teams" not in battle:
                        continue
                        
                    map_name = item.get("event", {}).get("map")
                    
                    # FILTRO DE REDUNDÂNCIA: Se o mapa já foi processado hoje para este alvo, salta a partida
                    if map_name in mapas_vistos:
                        continue
                        
                    # Registra o mapa como visto e prossegue com a extração
                    mapas_vistos.add(map_name)
                    
                    battle_time = item.get("battleTime")
                    mode = battle.get("mode")
                    duration = battle.get("duration", 0)
                    
                    todas_tags_partida = []
                    for team in battle["teams"]:
                        for player in team:
                            todas_tags_partida.append(player["tag"])
                            
                    match_hash = gerar_match_hash(battle_time, todas_tags_partida)
                    cur.execute(query_inserir_partida, (match_hash, battle_time, mode, map_name, duration))
                    
                    resultado_alvo = battle.get("result", "unknown")
                    team_do_alvo = None
                    
                    for tid, team in enumerate(battle["teams"]):
                        if any(p["tag"] == tag_alvo for p in team):
                            team_do_alvo = tid
                            break

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
                            
                            # AQUI ACONTECE A EXPANSÃO: Insere os novos jogadores na fila
                            cur.execute(query_inserir_jogador, (player_tag, player.get("name")))
                            
                            brawler = player.get("brawler", {})
                            dados_relacao = (
                                match_hash, player_tag, team_id, 
                                brawler.get("name"), brawler.get("power"), 
                                brawler.get("trophies"), resultado_time
                            )
                            cur.execute(query_inserir_relacao, dados_relacao)
                            
            elif resposta.status_code == 429:
                print("Limite de taxa da API excedido. A pausar por 10 segundos.")
                time.sleep(10)
                continue
                
            else:
                print(f"Erro {resposta.status_code} ignorado no alvo {tag_alvo}.")
                
            # 4. Marca o alvo atual como concluído (scanned = 1) para não o repetir
            cur.execute("UPDATE players SET scanned = 1 WHERE tag = ?", (tag_alvo,))
            conn.commit()
            
            alvos_processados += 1
            print(f"Progresso: {alvos_processados}/{LIMITE_POR_LOTE} processados.\n")
            
            time.sleep(1)

        print(f"Lote de {LIMITE_POR_LOTE} processado com sucesso. Paragem de segurança.")

    except KeyboardInterrupt:
        # Se você apertar Ctrl+C no terminal, ele cai aqui, salva o que fez e fecha limpo
        print("\n[Aviso] Interrupção manual detetada pelo utilizador.")
        print("A guardar o estado atual e a encerrar de forma segura...")
        conn.commit()

    finally:
        # Relatório final e encerramento
        cur.execute("SELECT COUNT(*) FROM match_players")    
        print("Total de registos na tabela match_players:", cur.fetchone()[0])
        conn.close()
        print("Ligação à base de dados encerrada.")