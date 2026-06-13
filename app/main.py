import streamlit as st
from streamlit_option_menu import option_menu

from app.views.meta_brawler_view import render_meta_brawler
from app.views.modes_view import render_modes
from app.views.trainer_view import render_trainer
from app.views.predictor_view import render_predictor
from i18n import init_language, t, switch_language
from views.meta_view import render_meta
from views.draft_view import render_draft

st.set_page_config(page_title="Brawl-ML Control", page_icon="robot", layout="wide")
init_language()

def fix_sidebar_width():
    st.markdown(
        """
        <style>
            /* 1. Trava a largura da sidebar */
            [data-testid="stSidebar"] {
                min-width: 400px !important;
                max-width: 400px !important;
                width: 400px !important;
            }
            
            /* 2. Impede que o texto de navegacao quebre a linha */
            [data-testid="stSidebarNav"] span {
                white-space: nowrap !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
            }
            
            /* 3. Prepara a barra lateral para ter flexibilidade vertical */
            [data-testid="stSidebarUserContent"] > div {
                display: flex;
                flex-direction: column;
                height: 88vh; 
            }
            
            /* 4. Localiza EXATAMENTE o widget de idioma e empurra-o para o fundo */
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
    page_meta = option_menu(
        menu_title=t("nav_metas"),
        options=[t("nav_meta"), t("nav_modes"), t("meta_brawler")], 
        icons=["bar-chart", "crosshair", "robot", "map", "trophy"],
        menu_icon="robot", 
        default_index=0, 
        styles={
            "container": {"padding": "5!important", "background-color": "transparent"},
            "icon": {"color": "#ffc107", "font-size": "20px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"0px"},
            "nav-link-selected": {"background-color": "#2e7bcf"},
        }
    )
    
with st.sidebar:
    page_simulators = option_menu(
        menu_title=t("nav_simulators"),
        options=[t("nav_predictor"), t("nav_draft")], 
        icons=["bar-chart", "crosshair", "robot", "map", "trophy"],
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
        "Language / Idioma", 
        options=['en', 'pt'], 
        format_func=lambda x: "English" if x == 'en' else "Português",
        index=0 if st.session_state['lang'] == 'en' else 1
    )
    
    if selected_language != st.session_state['lang']:
        switch_language(selected_language)
        st.rerun()

if page_meta == t("nav_meta"): render_meta()
elif page_meta == t("meta_brawler"): render_meta_brawler()
elif page_meta == t("nav_modes"): render_modes()

elif page_simulators == t("nav_draft"): render_draft()
elif page_simulators == t("nav_predictor"): render_predictor()