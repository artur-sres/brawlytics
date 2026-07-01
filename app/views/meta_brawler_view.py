import streamlit as st
import sqlite3
import pandas as pd
import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from utils import locate_file
from i18n import t

@st.cache_data
def extract_meta_brawler_statistics():
    """Queries SQLite for global brawler stats and computes a Meta Score."""
    db_path = locate_file('brawl_data.db') or locate_file('raw_events.sqlite')
    if not db_path:
        return pd.DataFrame()

    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        mp.brawler_name AS Brawler,
        COUNT(mp.match_hash) AS Total_Picks,
        SUM(CASE WHEN mp.result = 'victory' THEN 1 ELSE 0 END) AS Wins
    FROM match_players mp
    GROUP BY mp.brawler_name
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()

    if not df.empty:
        # 1. Filtro de significancia estatistica
        df = df[df['Total_Picks'] >= 10].copy()
        
        if df.empty:
            return df
            
        # 2. Calculo da Taxa de Vitoria
        df['Win_Rate'] = (df['Wins'] / df['Total_Picks']) * 100
        
        # 3. Normalizacao da Taxa de Escolha (O mais escolhido = 100)
        max_picks = df['Total_Picks'].max()
        df['Pick_Score'] = (df['Total_Picks'] / max_picks) * 100
        
        # 4. Calculo do Meta Score (60% Vitoria, 40% Presenca)
        df['Meta_Score'] = (df['Win_Rate'] * 0.6) + (df['Pick_Score'] * 0.4)
        
        # Arredondamento para apresentacao limpa
        df['Meta_Score'] = df['Meta_Score'].round(1)
        
    return df

def render_meta_brawler():
    spacer_left, main_col, spacer_right = st.columns([1, 4, 1])
    
    with main_col:
        st.title(t("meta_brawler_title"))
        st.markdown(t("meta_brawler_subtitle"))

        st.markdown("---")

        df_stats = extract_meta_brawler_statistics()

        if df_stats.empty:
            st.warning(t("warning_insufficient_data").format("Global"))
            st.stop()

        # Secao 1: O Podio dos Melhores (Top 3 Meta Score)
        st.header(t("best_in_game"))
        st.caption(t("meta_score_explanation"))
        
        top_3 = df_stats.sort_values(by='Meta_Score', ascending=False).head(3)
        cols_podium = st.columns(3)
        
        for i, (_, row) in enumerate(top_3.iterrows()):
            brawler = row['Brawler']
            score = row['Meta_Score']
            
            with cols_podium[i]:
                img_path = locate_file(f"{brawler.replace(' ', '_')}.webp")
                c_empty1, c_img, c_empty2 = st.columns([1, 2, 1])
                
                if img_path:
                    with c_img:
                        st.image(img_path, width='stretch')
                else:
                    with c_img:
                        no_photo_text = t("no_photo").format(brawler)
                        st.markdown(f"<div style='text-align: center; font-size: 10px; color: gray;'>{no_photo_text}</div>", unsafe_allow_html=True)
                
                st.markdown(f"<div style='text-align: center;'><b>{brawler}</b><br><span style='font-size: 1.1em; color: #2e7bcf;'><b>{score} Meta Score</b></span></div>", unsafe_allow_html=True)

        st.markdown("---")

        # Secao 2: Tabelas Detalhadas
        col_picks, col_wins, col_meta = st.columns(3, gap="medium")
        
        df_top_picks = df_stats.sort_values(by='Total_Picks', ascending=False).head(15)
        df_top_wins = df_stats.sort_values(by=['Win_Rate', 'Total_Picks'], ascending=[False, False]).head(15)
        df_top_meta = df_stats.sort_values(by='Meta_Score', ascending=False).head(15)
        
        with col_picks:
            st.subheader(t("most_picked"))
            st.dataframe(
                df_top_picks[['Brawler', 'Total_Picks']],
                column_config={
                    "Brawler": st.column_config.TextColumn(t("brawler")),
                    "Total_Picks": st.column_config.NumberColumn(t("matches"), format="%d")
                },
                hide_index=True,
                width='stretch'
            )
            
        with col_wins:
            st.subheader(t("highest_winrate"))
            st.dataframe(
                df_top_wins[['Brawler', 'Win_Rate']],
                column_config={
                    "Brawler": st.column_config.TextColumn(t("brawler")),
                    "Win_Rate": st.column_config.ProgressColumn(t("win_rate"), format="%.1f%%", min_value=0, max_value=100)
                },
                hide_index=True,
                width='stretch'
            )
            
        with col_meta:
            st.subheader(t("highest_meta_score"))
            st.dataframe(
                df_top_meta[['Brawler', 'Meta_Score']],
                column_config={
                    "Brawler": st.column_config.TextColumn(t("brawler")),
                    "Meta_Score": st.column_config.NumberColumn("Score", format="%.1f")
                },
                hide_index=True,
                width='stretch'
            )