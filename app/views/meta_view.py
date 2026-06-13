import streamlit as st
import sqlite3
import pandas as pd
import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from utils import locate_file, load_database_data
from i18n import t

@st.cache_data
def extract_map_statistics(mode, map_name):
    """Queries SQLite to get pick counts and win rates for a specific map."""
    db_path = locate_file('brawl_data.db') or locate_file('raw_events.sqlite')
    if not db_path: return pd.DataFrame()

    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        mp.brawler_name AS Brawler,
        COUNT(mp.match_hash) AS Total_Picks,
        SUM(CASE WHEN mp.result = 'victory' THEN 1 ELSE 0 END) AS Wins
    FROM match_players mp
    JOIN matches m ON mp.match_hash = m.match_hash
    WHERE m.mode = ? AND m.map = ?
    GROUP BY mp.brawler_name
    ORDER BY Total_Picks DESC
    """
    
    df = pd.read_sql_query(query, conn, params=(mode, map_name))
    conn.close()

    if not df.empty:
        df['Win_Rate'] = (df['Wins'] / df['Total_Picks']) * 100
        df = df[df['Total_Picks'] >= 3].copy()
        
    return df

def render_meta():
    spacer_left, main_col, spacer_right = st.columns([1, 4, 1])
    
    with main_col:
        st.title(t("meta_title"))
        st.markdown(t("meta_subtitle"))

        modes, maps_by_mode, _ = load_database_data()
        if not modes:
            st.error(t("error_empty_db"))
            st.stop()

        st.markdown("---")
        
        st.header(t("filter_scenario"))
        
        col_selectors, col_img = st.columns([1, 1.2], gap="large")
        
        with col_selectors:
            selected_mode = st.selectbox(
                t("game_mode"), 
                options=modes, 
                index=None, 
                placeholder="Selecione o modo...",
                key="meta_mode"
            )
            
            selected_map = st.selectbox(
                t("map"), 
                options=maps_by_mode.get(selected_mode, []) if selected_mode else [], 
                index=None, 
                placeholder="Selecione o mapa...",
                key="meta_map",
                disabled=not selected_mode
            )

        with col_img:
            default_img_path = locate_file("default_map.png") 
            
            if selected_map:
                map_img_path = locate_file(f"{selected_map.replace(' ', '_')}.png")
                if map_img_path:
                    st.image(map_img_path, width="stretch")
                elif default_img_path:
                    st.image(default_img_path, width="stretch")
            elif default_img_path:
                st.image(default_img_path, width="stretch")

        st.markdown("---")
        
        if not selected_mode or not selected_map:
            st.info(t('select_scenario'))
            st.stop()

        df_stats = extract_map_statistics(selected_mode, selected_map)

        if df_stats.empty:
            st.warning(t("warning_insufficient_data").format(selected_map))
            st.stop()

        st.subheader(f"{t('top_3_picks')}: {selected_map}")
        top_3 = df_stats.head(3)
        cols = st.columns(3)
        
        for i, (_, row) in enumerate(top_3.iterrows()):
            brawler = row['Brawler']
            wr = row['Win_Rate']
            with cols[i]:
                img_path = locate_file(f"{brawler.replace(' ', '_')}.webp")
                c_empty1, c_img, c_empty2 = st.columns([1, 2, 1])
                
                if img_path:
                    with c_img:
                        st.image(img_path, width="stretch")
                else:
                    with c_img:
                        no_photo_text = t("no_photo").format(brawler)
                        st.markdown(f"<div style='text-align: center; font-size: 10px; color: gray;'>{no_photo_text}</div>", unsafe_allow_html=True)
                
                st.markdown(f"<div style='text-align: center;'><b>{brawler}</b><br><span style='font-size: 0.9em;'>{wr:.1f}% WR</span></div>", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader(t('full_table'))
        
        # Substitui width="stretch" por width="stretch" (padrao atualizado do Streamlit)
        st.dataframe(
            df_stats,
            column_config={
                "Brawler": st.column_config.TextColumn(t("brawler")),
                "Total_Picks": st.column_config.NumberColumn(t("matches"), format="%d"),
                "Wins": None, 
                "Win_Rate": st.column_config.ProgressColumn(t("win_rate"), format="%.1f%%", min_value=0, max_value=100),
            },
            hide_index=True, 
            width="stretch"
        )