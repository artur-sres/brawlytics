import streamlit as st
import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from utils import locate_file, load_database_data, load_model
from data.prediction.predictor import calculate_static_probability, recommend_draft_brawlers
from i18n import t

def reset_draft():
    """Redefine as selecoes de Brawlers explicitamente para o valor padrao."""
    keys_to_clear = ['a1', 'a2', 'a3', 'e1', 'e2', 'e3']
    default_value = f"--- {t('empty')} ---"
    
    for key in keys_to_clear:
        if key in st.session_state:
            st.session_state[key] = default_value

def render_draft():
    spacer_left, main_col, spacer_right = st.columns([1, 4, 1])
    
    with main_col:
        st.title(t('draft_title'))
        st.markdown(t("draft_subtitle"))
        st.markdown(t("draft_subtitle_2"))

        modes, maps_by_mode, valid_brawlers = load_database_data()
        model, training_columns = load_model()

        if not model or not modes:
            st.error(t("error_missing_model"))
            st.stop()

        st.markdown("---")
        
        st.header(t('scenario'))
        
        col_selectors, col_img = st.columns([1, 1.2], gap="large")
        
        with col_selectors:
            selected_mode = st.selectbox(
                t("game_mode"), 
                options=modes, 
                index=None, 
                placeholder="Selecione o modo...",
                key="draft_mode"
            )
            
            selected_map = st.selectbox(
                t("map"), 
                options=maps_by_mode.get(selected_mode, []) if selected_mode else [], 
                index=None, 
                placeholder="Selecione o mapa...",
                key="draft_map",
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

        brawler_options = [f"--- {t('empty')} ---"] + valid_brawlers
        
        col_draft_header, col_draft_reset = st.columns([4, 1])
        with col_draft_header:
            st.header(t('draft_board'))
        with col_draft_reset:
            st.write("") 
            st.button(t('clear_brawlers'), on_click=reset_draft, width="stretch")

        col_t0, col_t1 = st.columns(2)

        with col_t0:
            st.subheader(t('allies'))
            a1 = st.selectbox("Slot 1:", brawler_options, index=0, key="a1")
            a2 = st.selectbox("Slot 2:", brawler_options, index=0, key="a2")
            a3 = st.selectbox("Slot 3:", brawler_options, index=0, key="a3")

        with col_t1:
            st.subheader(t('enemies'))
            e1 = st.selectbox("Slot 1:", brawler_options, index=0, key="e1")
            e2 = st.selectbox("Slot 2:", brawler_options, index=0, key="e2")
            e3 = st.selectbox("Slot 3:", brawler_options, index=0, key="e3")

        selected_allies = [b for b in [a1, a2, a3] if "---" not in b]
        selected_enemies = [b for b in [e1, e2, e3] if "---" not in b]
        all_selected = selected_allies + selected_enemies

        if len(set(all_selected)) < len(all_selected):
            st.markdown("---")
            st.error(t('error_duplicate_brawlers'))
            st.stop()

        st.markdown("---")
        
        if len(selected_allies) == 3 and len(selected_enemies) == 3:
            st.subheader(t('final_analysis'))
            prob_defeat, prob_victory = calculate_static_probability(
                model, training_columns, selected_mode, selected_map, selected_allies, selected_enemies
            )
            st.metric(label=t("win_chances"), value=f"{prob_victory:.1f}%")
            st.progress(int(prob_victory))
            
        elif len(selected_allies) < 3:
            st.subheader(t('team_recommendations'))
            
            top_5 = recommend_draft_brawlers(
                model, training_columns, selected_mode, selected_map, 
                selected_allies, selected_enemies, valid_brawlers
            )
            
            cols = st.columns(5)
            for i, (brawler, prob) in enumerate(top_5):
                with cols[i]:
                    img_path = locate_file(f"{brawler.replace(' ', '_')}.webp")
                    if img_path:
                        st.image(img_path, width="stretch")
                    st.markdown(f"<div style='text-align: center;'><b>{brawler}</b><br>{prob:.1f}%</div>", unsafe_allow_html=True)
                    
        elif len(selected_allies) == 3 and len(selected_enemies) < 3:
            # Captura o estado de limbo e orienta o utilizador
            st.info(t("select_remaining_enemies"))