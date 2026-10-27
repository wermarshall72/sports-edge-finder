import sqlite3
import pandas as pd
from datetime import datetime

DB_FILE = "bets_tracker.db"


def get_connection():
    """Opens a connection to our local SQLite database file."""
    return sqlite3.connect(DB_FILE)


def init_db():
    """Creates the bets and settings tables if they don't exist yet."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Create the main bets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            league TEXT NOT NULL,
            matchup TEXT NOT NULL,
            bet_type TEXT NOT NULL,
            pick TEXT NOT NULL,
            line REAL NOT NULL,
            odds INTEGER NOT NULL,
            stake REAL NOT NULL,
            sim_prob REAL NOT NULL,
            edge REAL NOT NULL,
            status TEXT DEFAULT 'Pending',
            profit REAL DEFAULT 0.0
        )
    """)

    # 2. Create the settings table (for storing Starting Bankroll)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value REAL NOT NULL
        )
    """)

    # Set a default $1,000 starting bankroll if not already set
    cursor.execute("""
        INSERT OR IGNORE INTO settings (key, value)
        VALUES ('starting_bankroll', 1000.0)
    """)

    conn.commit()
    conn.close()


def get_starting_bankroll() -> float:
    """Fetches your starting bankroll from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'starting_bankroll'")
    row = cursor.fetchone()
    conn.close()
    return float(row[0]) if row else 1000.0


def set_starting_bankroll(amount: float):
    """Updates your starting bankroll in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO settings (key, value)
        VALUES ('starting_bankroll', ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (float(amount),))
    conn.commit()
    conn.close()


def calculate_profit(stake: float, odds: int, status: str) -> float:
    """Calculates exact net dollar profit/loss based on American odds and bet outcome."""
    if status == "Won":
        if odds > 0:
            return round(stake * (odds / 100.0), 2)
        else:
            return round(stake * (100.0 / abs(odds)), 2)
    elif status == "Lost":
        return round(-stake, 2)
    else:
        # Pending or Push results in $0.00 net profit change
        return 0.0


def log_bet(league: str, matchup: str, bet_type: str, pick: str,
            line: float, odds: int, stake: float, sim_prob: float,
            edge: float, status: str = "Pending", date_str: str = None):
    """Saves a new bet into the SQLite ledger."""
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    profit = calculate_profit(stake, odds, status)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO bets (date, league, matchup, bet_type, pick, line, odds, stake, sim_prob, edge, status, profit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (date_str, league, matchup, bet_type, pick, line, odds, stake, sim_prob, edge, status, profit))
    conn.commit()
    conn.close()


def update_bet_status(bet_id: int, new_status: str):
    """Updates a bet's status (Pending/Won/Lost/Push) and recalculates its profit."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT stake, odds FROM bets WHERE id = ?", (bet_id,))
    row = cursor.fetchone()
    if row:
        stake, odds = row
        new_profit = calculate_profit(stake, odds, new_status)
        cursor.execute("""
            UPDATE bets
            SET status = ?, profit = ?
            WHERE id = ?
        """, (new_status, new_profit, bet_id))
        conn.commit()
    conn.close()


def delete_bet(bet_id: int):
    """Deletes a bet by ID if you ever make a typo."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bets WHERE id = ?", (bet_id,))
    conn.commit()
    conn.close()


def get_all_bets() -> pd.DataFrame:
    """Returns all logged bets as a Pandas DataFrame (table) for our Chrome dashboard."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM bets ORDER BY id DESC", conn)
    conn.close()
    return df


if __name__ == "__main__":
    init_db()
    print("✅ Database initialized successfully!")
    print(f"💰 Current Starting Bankroll: ${get_starting_bankroll():,.2f}")
