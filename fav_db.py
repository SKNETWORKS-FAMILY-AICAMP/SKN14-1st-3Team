# fav_db.py
from config import load_config
import mysql.connector


def _conn():
    return mysql.connector.connect(**load_config())


# ----------------------------------------------------------------—
def create_user_fav_table():
    """Create users + favourites tables if they don't exist."""
    cfg = load_config().copy()
    cfg.pop("database", None)
    with mysql.connector.connect(**cfg) as conn:
        cur = conn.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS parking_db")
        cur.execute("USE parking_db")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id       INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(40) UNIQUE,
                password VARCHAR(120)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user_favorites (
                user_id    INT,
                parking_id INT,
                PRIMARY KEY (user_id, parking_id)
            )
            """
        )
        conn.commit()


# ----------------------------------------------------------------—
def add_user(username: str, pw: str):
    """Insert a demo user (simple)."""
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT IGNORE INTO users (username, password) VALUES (%s,%s)",
            (username, pw),
        )
        conn.commit()


# ----------------------------------------------------------------—
def check_login(username: str, pw: str) -> bool:
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM users WHERE username=%s AND password=%s",
            (username, pw),
        )
        return cur.fetchone() is not None


# ----------------------------------------------------------------—
def add_to_favorite(username: str, parking_id: int):
    """Add to favourites; returns True on success."""
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username=%s", (username,))
        row = cur.fetchone()
        if not row:
            return False
        uid = row[0]
        cur.execute(
            "INSERT IGNORE INTO user_favorites (user_id, parking_id) VALUES (%s,%s)",
            (uid, parking_id),
        )
        conn.commit()
        return True


def get_favorite_list(username: str):
    with _conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id FROM users WHERE username=%s", (username,))
        row = cur.fetchone()
        if not row:
            return []
        uid = row["id"]
        cur.execute(
            """
            SELECT p.id, p.name, p.distance
            FROM user_favorites uf
            JOIN parking_info p ON p.id = uf.parking_id
            WHERE uf.user_id=%s
            ORDER BY p.distance
            """,
            (uid,),
        )
        return cur.fetchall()

def clear_favorites(username: str) -> None:
    """Delete every favourite row for the given user."""
    with _conn() as conn:
        cur = conn.cursor()
        # look up user id
        cur.execute("SELECT id FROM users WHERE username=%s", (username,))
        row = cur.fetchone()
        if not row:
            return
        uid = row[0]
        cur.execute("DELETE FROM user_favorites WHERE user_id=%s", (uid,))
        conn.commit()