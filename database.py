import aiosqlite
import os
from config import DB_PATH

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id    INTEGER PRIMARY KEY,
                username   TEXT,
                full_name  TEXT,
                joined_at  TEXT DEFAULT (datetime('now')),
                tests_done INTEGER DEFAULT 0,
                best_score INTEGER DEFAULT 0,
                last_subject TEXT DEFAULT ''
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER,
                subject    TEXT,
                variant    TEXT,
                primary_score INTEGER,
                test_score    INTEGER,
                max_score     INTEGER,
                done_at    TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS broadcasts (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                text       TEXT,
                sent_at    TEXT DEFAULT (datetime('now')),
                recipients INTEGER DEFAULT 0
            )
        """)
        await db.commit()

async def get_or_create_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?,?,?)",
            (user_id, username or "", full_name or "")
        )
        await db.execute(
            "UPDATE users SET username=?, full_name=? WHERE user_id=?",
            (username or "", full_name or "", user_id)
        )
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            if row:
                return dict(zip([c[0] for c in cur.description], row))
    return None

async def save_test_result(user_id, subject, variant, primary, test_score, max_score):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO test_results (user_id,subject,variant,primary_score,test_score,max_score) VALUES (?,?,?,?,?,?)",
            (user_id, subject, variant, primary, test_score, max_score)
        )
        await db.execute(
            "UPDATE users SET tests_done=tests_done+1, last_subject=? WHERE user_id=?",
            (subject, user_id)
        )
        await db.execute(
            "UPDATE users SET best_score=MAX(best_score,?) WHERE user_id=?",
            (test_score, user_id)
        )
        await db.commit()

async def get_user_stats(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT subject, COUNT(*) as cnt, MAX(test_score) as best FROM test_results WHERE user_id=? GROUP BY subject",
            (user_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(zip([c[0] for c in cur.description], r)) for r in rows]

async def get_all_user_ids():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cur:
            rows = await cur.fetchall()
            return [r[0] for r in rows]

async def count_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            row = await cur.fetchone()
            return row[0] if row else 0

async def get_all_results():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT subject, COUNT(*) as cnt, AVG(test_score) as avg FROM test_results GROUP BY subject"
        ) as cur:
            rows = await cur.fetchall()
            return [dict(zip([c[0] for c in cur.description], r)) for r in rows]
