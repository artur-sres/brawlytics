from data.collector.collector import fetch_battlelog, save_match
from data.database.db import init_db
from data.database.db import get_connection


def run():
    init_db()

    data = fetch_battlelog()
    if not data:
        return

    conn = get_connection()

    for item in data["items"]:
        save_match(conn, item)

    conn.close()
    print("Coleta finalizada com sucesso.")


if __name__ == "__main__":
    run()