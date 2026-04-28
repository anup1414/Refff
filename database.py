import sqlite3
import os
from config import DATABASE_NAME

def get_conn():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id        INTEGER PRIMARY KEY,
            username       TEXT,
            full_name      TEXT,
            balance        REAL    DEFAULT 0,
            total_earned   REAL    DEFAULT 0,
            refer_count    INTEGER DEFAULT 0,
            referred_by    INTEGER DEFAULT NULL,
            join_bonus     INTEGER DEFAULT 0,
            joined_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER,
            amount         REAL,
            upi_id         TEXT,
            status         TEXT DEFAULT 'pending',
            requested_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at   TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT,
            username TEXT UNIQUE,
            url      TEXT,
            type     TEXT DEFAULT 'channel'
        )
    """)

    conn.commit()
    conn.close()

# ── User Functions ───────────────────────────────────────────

def get_user(user_id):
    conn = get_conn()
    user = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return user

def add_user(user_id, username, full_name, referred_by=None):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, username, full_name, referred_by) VALUES (?,?,?,?)",
            (user_id, username, full_name, referred_by)
        )
        conn.commit()
    except Exception as e:
        print(f"add_user error: {e}")
    finally:
        conn.close()

def give_join_bonus(user_id, amount):
    conn = get_conn()
    conn.execute(
        "UPDATE users SET balance=balance+?, total_earned=total_earned+?, join_bonus=1 WHERE user_id=?",
        (amount, amount, user_id)
    )
    conn.commit()
    conn.close()

def add_refer_count(referrer_id, bonus_amount, refers_needed):
    """Refer count badhao, agar 10 ho gaye to bonus do"""
    conn = get_conn()
    conn.execute("UPDATE users SET refer_count=refer_count+1 WHERE user_id=?", (referrer_id,))
    user = conn.execute("SELECT refer_count FROM users WHERE user_id=?", (referrer_id,)).fetchone()
    bonus_given = False
    if user and user["refer_count"] % refers_needed == 0:
        conn.execute(
            "UPDATE users SET balance=balance+?, total_earned=total_earned+? WHERE user_id=?",
            (bonus_amount, bonus_amount, referrer_id)
        )
        bonus_given = True
    conn.commit()
    conn.close()
    return bonus_given

def update_balance(user_id, amount):
    conn = get_conn()
    conn.execute("UPDATE users SET balance=balance+?, total_earned=total_earned+? WHERE user_id=?",
                 (amount, amount, user_id))
    conn.commit()
    conn.close()

def deduct_balance(user_id, amount):
    conn = get_conn()
    conn.execute("UPDATE users SET balance=balance-? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_conn()
    users = conn.execute("SELECT user_id FROM users").fetchall()
    conn.close()
    return [u["user_id"] for u in users]

def get_stats():
    conn = get_conn()
    total_users    = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    total_earned   = conn.execute("SELECT SUM(total_earned) as s FROM users").fetchone()["s"] or 0
    pending_count  = conn.execute("SELECT COUNT(*) as c FROM withdrawals WHERE status='pending'").fetchone()["c"]
    approved_total = conn.execute("SELECT SUM(amount) as s FROM withdrawals WHERE status='approved'").fetchone()["s"] or 0
    conn.close()
    return total_users, total_earned, pending_count, approved_total

# ── Withdrawal Functions ─────────────────────────────────────

def create_withdrawal(user_id, amount, upi_id):
    conn = get_conn()
    conn.execute(
        "INSERT INTO withdrawals (user_id, amount, upi_id) VALUES (?,?,?)",
        (user_id, amount, upi_id)
    )
    conn.commit()
    conn.close()

def get_pending_withdrawals():
    conn = get_conn()
    rows = conn.execute(
        "SELECT w.*, u.full_name, u.username FROM withdrawals w JOIN users u ON w.user_id=u.user_id WHERE w.status='pending' ORDER BY w.requested_at"
    ).fetchall()
    conn.close()
    return rows

def update_withdrawal_status(wid, status):
    conn = get_conn()
    conn.execute(
        "UPDATE withdrawals SET status=?, processed_at=CURRENT_TIMESTAMP WHERE id=?",
        (status, wid)
    )
    conn.commit()
    conn.close()

def get_user_withdrawals(user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM withdrawals WHERE user_id=? ORDER BY requested_at DESC LIMIT 5",
        (user_id,)
    ).fetchall()
    conn.close()
    return rows

# ── Dynamic Channel Functions ────────────────────────────────

def get_db_channels():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM channels").fetchall()
    conn.close()
    return rows

def add_db_channel(name, username, url, ctype="channel"):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO channels (name, username, url, type) VALUES (?,?,?,?)",
                     (name, username, url, ctype))
        conn.commit()
        conn.close()
        return True
    except Exception:
        conn.close()
        return False

def remove_db_channel(username):
    conn = get_conn()
    conn.execute("DELETE FROM channels WHERE username=?", (username,))
    conn.commit()
    conn.close()
