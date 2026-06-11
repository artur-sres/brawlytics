import streamlit as st
import sys
import os

diretorio_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if diretorio_raiz not in sys.path:
    sys.path.append(diretorio_raiz)

from utils import localizar_arquivo, carregar_dados_banco, carregar_modelo
from data.prediction.predictor import calcular_probabilidade_estatica, recomendar_brawlers_draft

def renderizar_draft():
    st.title("🎯 Simulador de Draft Dinâmico")
    st.markdown("Recomendação matemática de escolhas em tempo real.")

    modos, mapas_por_modo, brawlers_validos = carregar_dados_banco()
    modelo, colunas_treino = carregar_modelo()

    if not modelo or not modos:
        st.error("Base de dados ou modelo ausente. Verifique a aba de Treino.")
        st.stop()

    st.header("🗺️ Cenário")
    col_modo, col_mapa = st.columns(2)
    with col_modo:
        modo_selecionado = st.selectbox("Modo de Jogo:", modos, key="draft_modo")
    with col_mapa:
        mapa_selecionado = st.selectbox("Mapa:", mapas_por_modo.get(modo_selecionado, []), key="draft_mapa")

    opcoes_brawlers = ["--- Vazio ---"] + brawlers_validos

    st.markdown("---")
    st.header("⚔️ Tabuleiro de Seleção")
    col_t0, col_t1 = st.columns(2)

    with col_t0:
        st.subheader("🔵 Aliados")
        a1 = st.selectbox("Slot 1:", opcoes_brawlers, index=0, key="a1")
        a2 = st.selectbox("Slot 2:", opcoes_brawlers, index=0, key="a2")
        a3 = st.selectbox("Slot 3:", opcoes_brawlers, index=0, key="a3")

    with col_t1:
        st.subheader("🔴 Inimigos")
        e1 = st.selectbox("Slot 1:", opcoes_brawlers, index=0, key="e1")
        e2 = st.selectbox("Slot 2:", opcoes_brawlers, index=0, key="e2")
        e3 = st.selectbox("Slot 3:", opcoes_brawlers, index=0, key="e3")

    aliados_selecionados = [b for b in [a1, a2, a3] if b != "--- Vazio ---"]
    inimigos_selecionados = [b for b in [e1, e2, e3] if b != "--- Vazio ---"]
    todos_selecionados = aliados_selecionados + inimigos_selecionados

    if len(set(todos_selecionados)) < len(todos_selecionados):
        st.error("⚠️ Existem Brawlers duplicados no draft.")
        st.stop()

    st.markdown("---")
    
    if len(aliados_selecionados) == 3 and len(inimigos_selecionados) == 3:
        st.subheader("📊 Análise Final da Partida")
        prob_derrota, prob_vitoria = calcular_probabilidade_estatica(
            modelo, colunas_treino, modo_selecionado, mapa_selecionado, aliados_selecionados, inimigos_selecionados
        )
        st.metric(label="Chances de Vitória (Aliados)", value=f"{prob_vitoria:.1f}%")
        st.progress(int(prob_vitoria))
        
    elif len(aliados_selecionados) < 3:
        st.subheader("💡 Recomendações para a sua Equipa")
        st.caption("A testar matematicamente as melhores sinergias...")
        
        top_5 = recomendar_brawlers_draft(
            modelo, colunas_treino, modo_selecionado, mapa_selecionado, 
            aliados_selecionados, inimigos_selecionados, brawlers_validos
        )
        
        cols = st.columns(5)
        for i, (brawler, prob) in enumerate(top_5):
            with cols[i]:
                caminho_img = localizar_arquivo(f"{brawler.replace(' ', '_')}.webp")
                if caminho_img:
                    st.image(caminho_img, use_container_width=True)
                st.markdown(f"<div style='text-align: center;'><b>{brawler}</b><br>{prob:.1f}%</div>", unsafe_allow_html=True)