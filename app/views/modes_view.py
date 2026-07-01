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
def extract_global_mode_statistics():
    """Queries SQLite to get aggregate pick counts and win rates per game mode."""
    db_path = locate_file('brawl_data.db') or locate_file('raw_events.sqlite')
    if not db_path: 
        return pd.DataFrame()

    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        m.mode AS Mode,
        mp.brawler_name AS Brawler,
        COUNT(mp.match_hash) AS Total_Picks,
        SUM(CASE WHEN mp.result = 'victory' THEN 1 ELSE 0 END) AS Wins
    FROM match_players mp
    JOIN matches m ON mp.match_hash = m.match_hash
    GROUP BY m.mode, mp.brawler_name
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()

    if not df.empty:
        df['Win_Rate'] = (df['Wins'] / df['Total_Picks']) * 100
        # Filtro de integridade estatistica: Remove brawlers com menos de 5 escolhas
        df = df[df['Total_Picks'] >= 5].copy()
        
    return df

def render_modes():
    spacer_left, main_col, spacer_right = st.columns([1, 4, 1])
    
    with main_col:
        st.title(t("modes_title"))
        st.markdown(t("modes_subtitle"))

        modes, _, _ = load_database_data()
        if not modes:
            st.error(t("error_empty_db"))
            st.stop()

        st.markdown("---")

        df_stats = extract_global_mode_statistics()

        if df_stats.empty:
            st.warning(t("warning_insufficient_data").format("Global"))
            st.stop()

        # Itera sobre cada modo para criar uma seccao dedicada
        for mode in modes:
            df_mode = df_stats[df_stats['Mode'] == mode]
            
            if df_mode.empty:
                continue
            
            st.header(mode.capitalize())
            
            col_picks, col_wins = st.columns(2, gap="large")
            
            # Extrai os Top 10 para cada categoria
            df_top_picks = df_mode.sort_values(by='Total_Picks', ascending=False).head(10)
            df_top_wins = df_mode.sort_values(by=['Win_Rate', 'Total_Picks'], ascending=[False, False]).head(10)
            
            with col_picks:
                st.subheader(t("most_picked"))
                st.dataframe(
                    df_top_picks[['Brawler', 'Total_Picks', 'Win_Rate']],
                    column_config={
                        "Brawler": st.column_config.TextColumn(t("brawler")),
                        "Total_Picks": st.column_config.NumberColumn(t("matches"), format="%d"),
                        "Win_Rate": st.column_config.ProgressColumn(t("win_rate"), format="%.1f%%", min_value=0, max_value=100),
                    },
                    hide_index=True,
                    width='stretch'
                )
            
            with col_wins:
                st.subheader(t("highest_winrate"))
                st.dataframe(
                    df_top_wins[['Brawler', 'Win_Rate', 'Total_Picks']],
                    column_config={
                        "Brawler": st.column_config.TextColumn(t("brawler")),
                        "Win_Rate": st.column_config.ProgressColumn(t("win_rate"), format="%.1f%%", min_value=0, max_value=100),
                        "Total_Picks": st.column_config.NumberColumn(t("matches"), format="%d"),
                    },
                    hide_index=True,
                    width='stretch'
                )
            
            st.markdown("---")