import streamlit as st
import sqlite3
import os
import sys

from data.training.train import treinar_modelo

# Garante que o interpretador reconhece a raiz do projeto para fazer os imports
diretorio_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if diretorio_raiz not in sys.path:
    sys.path.append(diretorio_raiz)

# Importa as funções originais do seu projeto
from data.collector.collector import executar_coleta
# IMPORTANTE: Descomente a linha abaixo e ajuste o nome da função de acordo com o seu train.py
# from data.training.train import sua_funcao_de_treino 

import streamlit as st
import sqlite3
import os
import sys

# Garante que o interpretador reconhece a raiz do projeto para fazer os imports
diretorio_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if diretorio_raiz not in sys.path:
    sys.path.append(diretorio_raiz)

# Importa as funções originais do seu projeto
from data.collector.collector import executar_coleta
# from data.training.train import sua_funcao_de_treino 

# Importa o motor de procura da nossa pasta app
from utils import localizar_arquivo

def obter_estatisticas_db():
    """Consulta a base de dados utilizando a nomenclatura correta do schema (match_hash)."""
    caminho_db = localizar_arquivo('brawl_data.db') or localizar_arquivo('raw_events.sqlite')
    
    if not caminho_db:
        return 0, 0
    
    conn = sqlite3.connect(caminho_db)
    cur = conn.cursor()
    
    try:
        # Correção: Alterado de match_id para match_hash de acordo com o schema.sql
        cur.execute("SELECT COUNT(DISTINCT match_hash) FROM matches")
        total_partidas = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(DISTINCT brawler_name) FROM match_players")
        total_brawlers = cur.fetchone()[0]
    except Exception as e:
        print(f"Erro ao ler base de dados: {e}")
        total_partidas, total_brawlers = 0, 0
        
    conn.close()
    return total_partidas, total_brawlers

import streamlit as st
import sqlite3
import os
import sys

# Garante o reconhecimento da raiz
diretorio_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if diretorio_raiz not in sys.path:
    sys.path.append(diretorio_raiz)

# Importações dos motores originais
from data.collector.collector import executar_coleta
from data.preprocessing.dataset_builder import construir_dataset # Confirme o nome da função no seu ficheiro
from data.training.train import treinar_modelo

from utils import localizar_arquivo


def renderizar_treinamento():
    st.title("⚙️ Painel de Controlo de IA")
    st.write("Efetue a gestão da base de dados e acione a re-calibragem do modelo preditivo.")
    
    total_partidas, total_brawlers = obter_estatisticas_db()
    
    st.markdown("---")
    st.subheader("📊 Saúde da Matriz de Dados")
    col1, col2 = st.columns(2)
    col1.metric("Partidas Únicas Recolhidas", total_partidas)
    col2.metric("Brawlers Mapeados", total_brawlers)
    
    if total_partidas < 7000:
        st.warning("⚠️ Volume Crítico: O modelo necessita de pelo menos 7.000 partidas para generalização matemática.")
    else:
        st.success("✅ Volume Ideal Alcançado.")
    
    st.markdown("---")
    st.subheader("🛠️ Operações de Engenharia (MLOps)")
    
    if st.button("📡 Executar Recolha de Dados (Crawler)", use_container_width=True):
        with st.spinner("A comunicar com a API da Supercell. Isto pode demorar alguns minutos..."):
            try:
                executar_coleta()
                st.success("Lote de dados recolhido com sucesso! Navegue para outra página e volte para atualizar os números.")
            except Exception as e:
                st.error(f"Falha técnica na recolha: {e}")
                
    # O botão de treino agora executa o pipeline completo
    if st.button("🧠 Compilar e Treinar IA", use_container_width=True):
        with st.spinner("Passo 1/2: A extrair dados do SQLite e a compilar a matriz CSV..."):
            try:
                # 1. Atualiza o CSV com as partidas novas
                construir_dataset() 
                
                with st.spinner("Passo 2/2: A treinar o algoritmo Gradient Boosting..."):
                    # 2. Treina o modelo com o CSV fresco
                    treinar_modelo()
                    
                st.success("✅ Pipeline concluído! Novo modelo gerado e guardado nos ficheiros .pkl.")
                st.info("Pode voltar ao separador 'Previsor de Partidas' para utilizar a inteligência atualizada.")
            except Exception as e:
                st.error(f"Erro durante o processo de treino: {e}")