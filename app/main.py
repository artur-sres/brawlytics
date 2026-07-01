import streamlit as st
from streamlit_option_menu import option_menu

from app.views.meta_brawler_view import render_meta_brawler
from app.views.modes_view import render_modes
from app.views.trainer_view import render_trainer
from app.views.predictor_view import render_predictor
from i18n import init_language, t, switch_language
from views.meta_view import render_meta
from views.draft_view import render_draft

st.set_page_config(page_title="Brawlytics", page_icon="robot", layout="wide")
init_language()

def fix_sidebar_width():
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                min-width: 400px !important;
                max-width: 400px !important;
                width: 400px !important;
            }
            
            [data-testid="stSidebarNav"] span {
                white-space: nowrap !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
            }
            
            [data-testid="stSidebarUserContent"] > div {
                display: flex;
                flex-direction: column;
                height: 88vh; 
            }
            
            [data-testid="stSidebarUserContent"] div[data-testid="stElementContainer"]:has([data-testid="stSelectbox"]) {
                margin-top: auto !important;
                padding-bottom: 20px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

fix_sidebar_width()

with st.sidebar:
    nav = option_menu(
        menu_title=t("nav"),
        options=[t("meta_brawlers"), t("meta_brawlers_mode"), t("meta_brawlers_map"), t("win_predictor"), t("draft_simulator")], 
        icons=["bar-chart", "crosshair", "map", "robot", "trophy"],
        menu_icon="robot", 
        default_index=0, 
        styles={
            "container": {"padding": "5!important", "background-color": "transparent"},
            "icon": {"color": "#ffc107", "font-size": "20px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"0px"},
            "nav-link-selected": {"background-color": "#2e7bcf"},
        }
    )
    
    
    selected_language = st.selectbox(
        t("language"), 
        options=['en', 'pt'], 
        format_func=lambda x: t("english") if x == 'en' else t("portuguese"),
        index=0 if st.session_state['lang'] == 'en' else 1
    )
    
    if selected_language != st.session_state['lang']:
        switch_language(selected_language)
        st.rerun()

if nav == t("meta_brawlers"): render_meta_brawler()
elif nav == t("meta_brawlers_mode"): render_modes()
elif nav == t("meta_brawlers_map"): render_meta()
elif nav == t("win_predictor"): render_predictor()
elif nav == t("draft_simulator"): render_draft()