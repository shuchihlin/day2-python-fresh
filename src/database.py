import aiosqlite
from typing import Optional


class Database:
    def __init__(self, db_path: str = "app.db"):
        self.db_path = db_path
        self.conn = None

    async def connect(self):
        """Initialize database connection and create tables."""
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row
        await self._create_tables()

    async def disconnect(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()

    async def _create_tables(self):
        """Create database schema."""
        await self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        await self.conn.commit()

    async def create_user(self, email: str, name: str, password_hash: str) -> int:
        """Create a new user. Returns user ID."""
        cursor = await self.conn.execute(
            "INSERT INTO users (email, name, password) VALUES (?, ?, ?)",
            (email, name, password_hash),
        )
        await self.conn.commit()
        return cursor.lastrowid

    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Fetch user by email."""
        cursor = await self.conn.execute(
            "SELECT id, email, name, password FROM users WHERE email = ?", (email,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """Fetch user by ID."""
        cursor = await self.conn.execute(
            "SELECT id, email, name FROM users WHERE id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def update_user_password(self, email: str, password_hash: str) -> bool:
        """Update user password. Returns True if updated."""
        cursor = await self.conn.execute(
            "UPDATE users SET password = ? WHERE email = ?", (password_hash, email)
        )
        await self.conn.commit()
        return cursor.rowcount > 0

    async def get_user_posts(self, user_id: int) -> list:
        """Fetch all posts for a user."""
        cursor = await self.conn.execute(
            "SELECT id, title, content FROM posts WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def create_reset_token(
        self, email: str, token: str, expires_at: str
    ) -> bool:
        """Store password reset token."""
        try:
            await self.conn.execute(
                "INSERT INTO reset_tokens (email, token, expires_at) VALUES (?, ?, ?)",
                (email, token, expires_at),
            )
            await self.conn.commit()
            return True
        except Exception:
            return False

    async def verify_reset_token(self, token: str) -> Optional[str]:
        """Verify reset token and return email if valid."""
        cursor = await self.conn.execute(
            "SELECT email FROM reset_tokens WHERE token = ? AND expires_at > datetime('now')",
            (token,),
        )
        row = await cursor.fetchone()
        if row:
            await self.conn.execute(
                "DELETE FROM reset_tokens WHERE token = ?", (token,)
            )
            await self.conn.commit()
            return row[0]
        return None
