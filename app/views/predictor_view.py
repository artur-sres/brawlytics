import streamlit as st
import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from utils import locate_file, load_database_data, load_model
from data.prediction.predictor import calculate_static_probability
from i18n import t

def reset_predictor():
    """Redefine as selecoes de Brawlers explicitamente para o valor padrao."""
    keys_to_clear = ['p_a1', 'p_a2', 'p_a3', 'p_e1', 'p_e2', 'p_e3']
    default_value = f"--- {t('empty')} ---"
    
    for key in keys_to_clear:
        if key in st.session_state:
            st.session_state[key] = default_value

def render_predictor():
    spacer_left, main_col, spacer_right = st.columns([1, 4, 1])
    
    with main_col:
        st.title(t("predictor_title"))
        st.markdown(t("predictor_subtitle"))

        modes, maps_by_mode, valid_brawlers = load_database_data()
        model, training_columns = load_model()

        if not modes:
            st.error(t("error_empty_db"))
            st.stop()

        if not model:
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
                placeholder=t("select_mode"),
                key="pred_mode"
            )
            
            selected_map = st.selectbox(
                t("map"), 
                options=maps_by_mode.get(selected_mode, []) if selected_mode else [], 
                index=None, 
                placeholder=t("select_map"),
                key="pred_map",
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

        col_pred_header, col_pred_reset = st.columns([4, 1])
        with col_pred_header:
            st.header(t('compositions'))
        with col_pred_reset:
            st.write("") 
            st.button(t('clear_brawlers'), on_click=reset_predictor, width="stretch")

        col_t0, col_t1 = st.columns(2)

        with col_t0:
            st.subheader(t('your_team'))
            p_a1 = st.selectbox(t("ally").format(1), brawler_options, index=0, key="p_a1")
            p_a2 = st.selectbox(t("ally").format(2), brawler_options, index=0, key="p_a2")
            p_a3 = st.selectbox(t("ally").format(3), brawler_options, index=0, key="p_a3")
            
            cols_img_t0 = st.columns(3)
            for i, brawler in enumerate([p_a1, p_a2, p_a3]):
                if "---" not in brawler:
                    brawler_path = locate_file(f"{brawler.replace(' ', '_')}.webp")
                    if brawler_path:
                        cols_img_t0[i].image(brawler_path, width="stretch")
                    else:
                        no_photo_text = t("no_photo").format(brawler)
                        cols_img_t0[i].markdown(f"<div style='text-align: center; font-size: 10px; color: gray;'>{no_photo_text}</div>", unsafe_allow_html=True)

        with col_t1:
            st.subheader(t('enemy_team'))
            p_e1 = st.selectbox(t("opponent").format(1), brawler_options, index=0, key="p_e1")
            p_e2 = st.selectbox(t("opponent").format(2), brawler_options, index=0, key="p_e2")
            p_e3 = st.selectbox(t("opponent").format(3), brawler_options, index=0, key="p_e3")
            
            cols_img_t1 = st.columns(3)
            for i, brawler in enumerate([p_e1, p_e2, p_e3]):
                if "---" not in brawler:
                    brawler_path = locate_file(f"{brawler.replace(' ', '_')}.webp")
                    if brawler_path:
                        cols_img_t1[i].image(brawler_path, width="stretch")
                    else:
                        no_photo_text = t("no_photo").format(brawler)
                        cols_img_t1[i].markdown(f"<div style='text-align: center; font-size: 10px; color: gray;'>{no_photo_text}</div>", unsafe_allow_html=True)

        selected_allies = [b for b in [p_a1, p_a2, p_a3] if "---" not in b]
        selected_enemies = [b for b in [p_e1, p_e2, p_e3] if "---" not in b]
        all_selected = selected_allies + selected_enemies

        st.markdown("---")
        
        if st.button(t('calculate_win_probability'), width="stretch"):
            if len(set(all_selected)) < len(all_selected):
                st.error(t('error_duplicate_brawlers'))
            elif len(selected_allies) < 3 or len(selected_enemies) < 3:
                st.warning(t("select_all_brawlers"))
            else:
                st.subheader(t('analysis_result'))
                prob_defeat, prob_victory = calculate_static_probability(
                    model, training_columns, selected_mode, selected_map, selected_allies, selected_enemies
                )
                st.metric(label=t("win_chances"), value=f"{prob_victory:.1f}%")
                st.progress(int(prob_victory))
                
                if prob_victory > 55:
                    st.success(t("verdict_superior"))
                elif prob_defeat > 55:
                    st.error(t("verdict_disadvantage"))
                else:
                    st.warning(t("verdict_balanced"))
        else:
            if len(selected_allies) < 3 or len(selected_enemies) < 3:
                st.info(t("select_all_brawlers"))