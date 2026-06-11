import sqlite3
import os

DIR_ATUAL = os.path.dirname(__file__)
SCHEMA_PATH = os.path.join(DIR_ATUAL, "schema.sql")

# Garante que o banco seja criado na raiz do projeto (duas pastas acima do db.py)
RAIZ_PROJETO = os.path.abspath(os.path.join(DIR_ATUAL, "..", ".."))
DB_PATH = os.path.join(RAIZ_PROJETO, "brawl_data.db")

def get_connection():
    """Estabelece e retorna a conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_PATH)
    return conn

def initdb():
    conn = get_connection()
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()