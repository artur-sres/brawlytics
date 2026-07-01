import pandas as pd
import os
import sys
import hashlib

# Ensures the root directory is recognized for absolute imports
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from data.database.db import get_connection

def clean_community_maps(df):
    """
    Removes matches played on community maps from the DataFrame,
    using the assets/maps folder as the single source of truth.
    """
    maps_folder = os.path.join(root_dir, 'assets', 'maps')
    
    official_maps = []
    if os.path.exists(maps_folder):
        for filename in os.listdir(maps_folder):
            if filename.lower().endswith('.png'):
                clean_name = filename[:-4].replace('_', ' ')
                official_maps.append(clean_name)
                
    initial_rows = len(df)
    clean_df = df[df['map'].isin(official_maps)]
    rows_removed = initial_rows - len(clean_df)
    
    print(f"Noise Filter: {rows_removed} matches on community maps were ignored.")
    return clean_df

def build_dataset():
    """Extracts relational data from the database and compiles the CSV matrix."""
    print("Extracting relational data from the database...")
    conn = get_connection()
    
    # Blacklist of non-competitive or irrelevant modes
    ignored_modes = ('duoShowdown', 'soloShowdown', 'siege', 'bigGame', 'bossFight', 'roboRumble')
    
    query = f"""
    SELECT 
        m.match_hash, m.mode, m.map, 
        mp.team_id, mp.brawler_name, mp.result
    FROM matches m
    JOIN match_players mp ON m.match_hash = mp.match_hash
    WHERE m.mode NOT IN {ignored_modes}
    """
    df_raw = pd.read_sql_query(query, conn)
    conn.close()

    if df_raw.empty:
        print("Error: The database contains no data to process.")
        return

    print(f"Extracted {len(df_raw)} raw rows. Starting Feature Engineering...")
    
    flat_data = []
    grouped = df_raw.groupby('match_hash')

    for match_hash, group in grouped:
        # Ensures only full 3v3 matches are processed
        if len(group) != 6:
            continue

        match_info = group.iloc[0]
        mode = match_info['mode']
        map_name = match_info['map']

        t0 = group[group['team_id'] == 0]
        t1 = group[group['team_id'] == 1]

        if len(t0) != 3 or len(t1) != 3:
            continue

        brawlers_t0 = t0['brawler_name'].tolist()
        brawlers_t1 = t1['brawler_name'].tolist()
        
        # Permutational Invariance: Sorts names alphabetically so order doesn't matter
        brawlers_t0.sort()
        brawlers_t1.sort()

        result_t0 = t0['result'].iloc[0]

        if result_t0 in ['draw', 'unknown']:
            continue 

        target = 1 if result_t0 == 'victory' else 0

        # Anti-Bias Shuffle: team_id 0 originally correlates with the crawler's
        # target player's team (and thus with stronger players), creating a
        # ~55/45 victory skew. We deterministically swap "team 0" and "team 1"
        # based on the match_hash, so the label no longer leaks "who was the
        # crawler's seed player".
        swap = int(hashlib.sha256(match_hash.encode('utf-8')).hexdigest(), 16) % 2 == 1
        if swap:
            brawlers_t0, brawlers_t1 = brawlers_t1, brawlers_t0
            target = 1 - target

        # Assembly of the final matrix (Pure Meta: no power or trophies)
        flat_data.append({
            'match_hash': match_hash,
            'mode': mode,
            'map': map_name,
            't0_brawler_1': brawlers_t0[0],
            't0_brawler_2': brawlers_t0[1],
            't0_brawler_3': brawlers_t0[2],
            't1_brawler_1': brawlers_t1[0],
            't1_brawler_2': brawlers_t1[1],
            't1_brawler_3': brawlers_t1[2],
            'target': target
        })

    dataset = pd.DataFrame(flat_data)
    
    # 1. Apply Community Maps Filter
    dataset = clean_community_maps(dataset)
    
    # 2. Export to CSV
    csv_path = os.path.join(root_dir, 'data', 'storage', 'dataset_brawl.csv')
    dataset.to_csv(csv_path, index=False)
    
    print(f"\nDataset processed successfully!")
    print(f"Total clean and valid matches for training: {len(dataset)}")

if __name__ == "__main__":
    build_dataset()