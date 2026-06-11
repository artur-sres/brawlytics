import streamlit as st
import pandas as pd
from utils import localizar_arquivo, carregar_dados_banco, carregar_modelo

def renderizar_previsor():
    st.title("🤖 Previsor de Partidas 3v3")
    st.markdown("Analise composições do **Brawl Stars** com Inteligência Artificial.")

    modos, mapas_por_modo, brawlers_validos = carregar_dados_banco()
    modelo, colunas_treino = carregar_modelo()

    if not modos:
        st.error(" Banco de dados não encontrado. Rode o Crawler primeiro.")
        st.stop()

    if not modelo:
        st.error(" Artefatos da IA (.pkl) não encontrados. Treine o modelo primeiro.")
        st.stop()

    # 1. SEÇÃO DE MAPA E MODO
    st.header("🗺️ Cenário")
    col_modo, col_mapa = st.columns(2)

    with col_modo:
        modo_selecionado = st.selectbox("Modo de Jogo:", modos)

    with col_mapa:
        mapas_disponiveis = mapas_por_modo.get(modo_selecionado, [])
        mapa_selecionado = st.selectbox("Mapa:", mapas_disponiveis)

    caminho_imagem_mapa = localizar_arquivo(f"{mapa_selecionado.replace(' ', '_')}.png")
    if caminho_imagem_mapa:
        st.image(caminho_imagem_mapa, caption=mapa_selecionado, use_container_width=True)
    else:
        st.info(f"💡 Imagem do mapa não encontrada: {mapa_selecionado}.png")

    # 2. SEÇÃO DE EQUIPES
    st.header("⚔️ Composições")
    col_t0, col_t1 = st.columns(2)

    with col_t0:
        st.subheader("🔵 Sua Equipe")
        t0_b1 = st.selectbox("Aliado 1:", brawlers_validos, index=0)
        t0_b2 = st.selectbox("Aliado 2:", brawlers_validos, index=1)
        t0_b3 = st.selectbox("Aliado 3:", brawlers_validos, index=2)
        
        cols_img_t0 = st.columns(3)
        for i, brawler in enumerate([t0_b1, t0_b2, t0_b3]):
            caminho_brawler = localizar_arquivo(f"{brawler.replace(' ', '_')}.webp")
            if caminho_brawler:
                cols_img_t0[i].image(caminho_brawler, use_container_width=True)
            else:
                cols_img_t0[i].markdown(f"<div style='text-align: center; font-size: 10px; color: gray;'>Sem foto<br>({brawler})</div>", unsafe_allow_html=True)

    with col_t1:
        st.subheader("🔴 Equipe Inimiga")
        t1_b1 = st.selectbox("Adversário 1:", brawlers_validos, index=3)
        t1_b2 = st.selectbox("Adversário 2:", brawlers_validos, index=4)
        t1_b3 = st.selectbox("Adversário 3:", brawlers_validos, index=5)
        
        cols_img_t1 = st.columns(3)
        for i, brawler in enumerate([t1_b1, t1_b2, t1_b3]):
            caminho_brawler = localizar_arquivo(f"{brawler.replace(' ', '_')}.webp")
            if caminho_brawler:
                cols_img_t1[i].image(caminho_brawler, use_container_width=True)
            else:
                cols_img_t1[i].markdown(f"<div style='text-align: center; font-size: 10px; color: gray;'>Sem foto<br>({brawler})</div>", unsafe_allow_html=True)

    # 3. MOTOR DE INFERÊNCIA
    st.markdown("---")
    if st.button("🧠 Calcular Probabilidade de Vitória", use_container_width=True):
        equipe_0 = [t0_b1, t0_b2, t0_b3]
        equipe_1 = [t1_b1, t1_b2, t1_b3]
        
        if len(set(equipe_0)) < 3 or len(set(equipe_1)) < 3:
            st.warning("⚠️ O Brawl Stars não permite Brawlers repetidos na mesma equipe. Ajuste a composição.")
        else:
            entrada = pd.DataFrame(0, index=[0], columns=colunas_treino)
            
            if f'mode_{modo_selecionado}' in colunas_treino: entrada.at[0, f'mode_{modo_selecionado}'] = 1
            if f'map_{mapa_selecionado}' in colunas_treino: entrada.at[0, f'map_{mapa_selecionado}'] = 1
            if 'delta_power' in colunas_treino: entrada.at[0, 'delta_power'] = 0.0
            if 'delta_trophies' in colunas_treino: entrada.at[0, 'delta_trophies'] = 0.0
            for b in equipe_0:
                if f't0_{b}' in colunas_treino: entrada.at[0, f't0_{b}'] = 1
            for b in equipe_1:
                if f't1_{b}' in colunas_treino: entrada.at[0, f't1_{b}'] = 1
                
            probabilidades = modelo.predict_proba(entrada)[0]
            prob_derrota = probabilidades[0] * 100
            prob_vitoria = probabilidades[1] * 100
            
            st.subheader("📊 Resultado da Análise")
            st.metric(label="Chances de Vitória (Sua Equipe)", value=f"{prob_vitoria:.1f}%")
            st.progress(int(prob_vitoria))
            
            if prob_vitoria > 55:
                st.success("Veredito: Composição superior. Vantagem sólida para a Sua Equipe!")
            elif prob_derrota > 55:
                st.error("Veredito: Desvantagem estrutural. A Equipe Inimiga tem controle da partida.")
            else:
                st.warning("Veredito: Partida altamente equilibrada. O resultado dependerá puramente da habilidade dos jogadores.")