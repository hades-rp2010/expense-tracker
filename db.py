import sqlite3
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).parent / "expenses.db"

DEFAULT_CATEGORIES = [
    "Groceries & Food",
    "Dining Out",
    "Transport & Travel",
    "Housing & Rent",
    "Utilities & Bills",
    "Shopping & Personal",
    "Entertainment & Leisure",
    "Healthcare & Fitness",
    "Subscriptions",
    "Miscellaneous",
]

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                expense_date TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Populate default categories if table is empty
        cursor.execute("SELECT COUNT(*) as count FROM categories")
        if cursor.fetchone()["count"] == 0:
            cursor.executemany(
                "INSERT OR IGNORE INTO categories (name) VALUES (?)",
                [(c,) for c in DEFAULT_CATEGORIES],
            )
        conn.commit()

def get_categories() -> List[str]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM categories ORDER BY name ASC")
        return [row["name"] for row in cursor.fetchall()]

def add_category(name: str) -> bool:
    clean_name = name.strip()
    if not clean_name:
        return False
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (clean_name,))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False

def add_expense(amount: float, category: str, expense_date: date, notes: Optional[str] = None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO expenses (amount, category, expense_date, notes)
            VALUES (?, ?, ?, ?)
            """,
            (float(amount), category, expense_date.isoformat(), notes or ""),
        )
        conn.commit()

def get_expenses(start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT id, amount, category, expense_date, notes, created_at FROM expenses"
        params = []
        conditions = []
        if start_date:
            conditions.append("expense_date >= ?")
            params.append(start_date.isoformat())
        if end_date:
            conditions.append("expense_date <= ?")
            params.append(end_date.isoformat())
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY expense_date DESC, id DESC"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

def update_expense(expense_id: int, amount: float, category: str, expense_date: date, notes: Optional[str] = None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE expenses
            SET amount = ?, category = ?, expense_date = ?, notes = ?
            WHERE id = ?
            """,
            (float(amount), category, expense_date.isoformat() if isinstance(expense_date, (date, datetime)) else str(expense_date), notes or "", expense_id),
        )
        conn.commit()

def delete_expense(expense_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()

