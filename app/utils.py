import os
import sqlite3
import joblib
import streamlit as st

def localizar_arquivo(nome_arquivo):
    """Varre todo o projeto autonomamente à procura do ficheiro, ignorando maiúsculas/minúsculas."""
    diretorio_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Converte o nome procurado para minúsculas logo à partida
    nome_procurado_lower = nome_arquivo.lower()
    
    for root, dirs, files in os.walk(diretorio_raiz):
        for file in files:
            # Compara a versão minúscula do ficheiro atual com o procurado
            if file.lower() == nome_procurado_lower:
                return os.path.join(root, file)
                
    return None

@st.cache_data
def carregar_dados_banco():
    """Lê a base de dados em cache e filtra os modos indesejados."""
    caminho_db = localizar_arquivo('brawl_data.db') or localizar_arquivo('raw_events.sqlite')
    if not caminho_db:
        return [], {}, []

    conn = sqlite3.connect(caminho_db)
    cur = conn.cursor()

    # Blacklist para a interface
    MODOS_IGNORADOS = ['duoShowdown', 'soloShowdown', 'siege', 'bigGame', 'bossFight', 'roboRumble']

    cur.execute("SELECT DISTINCT mode FROM matches")
    modos_brutos = [row[0] for row in cur.fetchall()]
    
    # Filtra: Só guarda o modo se ele NÃO estiver na blacklist
    modos = [m for m in modos_brutos if m not in MODOS_IGNORADOS]

    mapas_por_modo = {}
    for modo in modos:
        cur.execute("SELECT DISTINCT map FROM matches WHERE mode = ?", (modo,))
        mapas_por_modo[modo] = [row[0] for row in cur.fetchall()]

    cur.execute("SELECT DISTINCT brawler_name FROM match_players")
    brawlers_validos = sorted([row[0].upper() for row in cur.fetchall()])

    conn.close()
    return modos, mapas_por_modo, brawlers_validos

@st.cache_resource
def carregar_modelo():
    """Lê a matriz matemática da Inteligência Artificial em cache."""
    caminho_modelo = localizar_arquivo('modelo_brawl.pkl') or localizar_arquivo('classifier_gb_v1.pkl')
    caminho_colunas = localizar_arquivo('colunas_brawl.pkl') or localizar_arquivo('feature_names_v1.pkl')
    
    if caminho_modelo and caminho_colunas:
        modelo = joblib.load(caminho_modelo)
        colunas = joblib.load(caminho_colunas)
        return modelo, colunas
    return None, None