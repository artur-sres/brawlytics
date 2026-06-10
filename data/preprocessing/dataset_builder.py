import pandas as pd
import os
from data.database.db import get_connection

def construir_dataset():
    print("A extrair dados relacionais da base de dados...")
    conn = get_connection()
    
    # 1. Nova Query: Agora inclui 'power' e 'trophies'
    query = """
    SELECT 
        m.match_hash, m.mode, m.map, 
        mp.team_id, mp.brawler_name, mp.power, mp.trophies, mp.result
    FROM matches m
    JOIN match_players mp ON m.match_hash = mp.match_hash
    """
    df_raw = pd.read_sql_query(query, conn)
    conn.close()

    if df_raw.empty:
        print("Erro: A base de dados não contém dados para processar.")
        return

    print(f"Extraídas {len(df_raw)} linhas brutas. A iniciar engenharia de variáveis (Feature Engineering)...")
    
    dados_planos = []
    agrupado = df_raw.groupby('match_hash')

    for match_hash, grupo in agrupado:
        if len(grupo) != 6:
            continue

        info_partida = grupo.iloc[0]
        modo = info_partida['mode']
        mapa = info_partida['map']

        t0 = grupo[grupo['team_id'] == 0]
        t1 = grupo[grupo['team_id'] == 1]

        if len(t0) != 3 or len(t1) != 3:
            continue

        brawlers_t0 = t0['brawler_name'].tolist()
        brawlers_t1 = t1['brawler_name'].tolist()
        
        # Invariância Permutacional
        brawlers_t0.sort()
        brawlers_t1.sort()

        # 2. ENGENHARIA DE VARIÁVEIS: Cálculo de Vantagem Técnica
        # Extrai a média de poder e troféus. O .fillna(0) evita quebras se a API falhar no envio do dado.
        power_t0 = t0['power'].fillna(0).mean()
        power_t1 = t1['power'].fillna(0).mean()
        
        trophies_t0 = t0['trophies'].fillna(0).mean()
        trophies_t1 = t1['trophies'].fillna(0).mean()

        # Cria a variável contínua de Diferencial (Delta)
        delta_power = power_t0 - power_t1
        delta_trophies = trophies_t0 - trophies_t1

        resultado_t0 = t0['result'].iloc[0]

        if resultado_t0 in ['draw', 'unknown']:
            continue 

        target = 1 if resultado_t0 == 'victory' else 0

        # Montagem da matriz final
        dados_planos.append({
            'match_hash': match_hash,
            'mode': modo,
            'map': mapa,
            't0_brawler_1': brawlers_t0[0],
            't0_brawler_2': brawlers_t0[1],
            't0_brawler_3': brawlers_t0[2],
            't1_brawler_1': brawlers_t1[0],
            't1_brawler_2': brawlers_t1[1],
            't1_brawler_3': brawlers_t1[2],
            'delta_power': round(delta_power, 2), # Reduz as casas decimais para otimização
            'delta_trophies': round(delta_trophies, 2),
            'target': target
        })

    dataset = pd.DataFrame(dados_planos)
    
    diretorio_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    caminho_csv = os.path.join(diretorio_raiz, 'dataset_brawl.csv')
    
    dataset.to_csv(caminho_csv, index=False)
    print(f"\nDataset processado com sucesso!")
    print(f"Total de partidas limpas e válidas para treino: {len(dataset)}")

if __name__ == "__main__":
    construir_dataset()