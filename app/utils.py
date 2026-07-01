import os
import sqlite3
import joblib
import streamlit as st

def locate_file(filename):
    """Scans the entire project to find the file, ignoring case sensitivity."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    target_name_lower = filename.lower()
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.lower() == target_name_lower:
                return os.path.join(root, file)
                
    return None

@st.cache_data
def load_database_data():
    """Reads the database in cache and filters out unwanted modes and community maps."""
    db_path = locate_file('brawl_data.db') or locate_file('raw_events.sqlite')
    if not db_path:
        return [], {}, []

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    IGNORED_MODES = ['duoShowdown', 'soloShowdown', 'siege', 'bigGame', 'bossFight', 'roboRumble']

    cur.execute("SELECT DISTINCT mode FROM matches")
    raw_modes = [row[0] for row in cur.fetchall()]
    modes = [m for m in raw_modes if m not in IGNORED_MODES]

    maps_by_mode = {}
    for mode in modes:
        cur.execute("SELECT DISTINCT map FROM matches WHERE mode = ?", (mode,))
        raw_maps = [row[0] for row in cur.fetchall()]
        
        official_maps = []
        for b_map in raw_maps:
            if locate_file(f"{b_map.replace(' ', '_')}.png"):
                official_maps.append(b_map)
        
        if official_maps:
            maps_by_mode[mode] = official_maps

    cur.execute("SELECT DISTINCT brawler_name FROM match_players")
    valid_brawlers = sorted([row[0].upper() for row in cur.fetchall()])

    conn.close()
    return modes, maps_by_mode, valid_brawlers

@st.cache_resource
def load_model():
    """Loads the model and columns directly from the data/storage folder."""
    base_storage = os.path.join(os.path.dirname(__file__), '..', 'data', 'storage')
    
    model_path = os.path.join(base_storage, 'model.pkl')
    columns_path = os.path.join(base_storage, 'columns.pkl')
    
    if os.path.exists(model_path) and os.path.exists(columns_path):
        model = joblib.load(model_path)
        columns = joblib.load(columns_path)
        return model, columns
    
    return None, None