from pathlib import Path
from dotenv import load_dotenv
import os
import mariadb
import sys

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": 3306,
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "PokemonRivalry"),
}


def get_connection():
    try:
        conn = mariadb.connect(**DB_CONFIG)
        conn.autocommit = True
        return conn
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        sys.exit(1)
