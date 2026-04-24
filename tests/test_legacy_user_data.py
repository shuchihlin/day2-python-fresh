import pytest
import sqlite3
from src.legacy_user_data import fetch_user_by_id, fetch_user_posts, fetch_user_with_posts


def create_test_db():
    """Create in-memory test database with sample data."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    cursor.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL)"
    )
    cursor.execute(
        "CREATE TABLE posts (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, title TEXT NOT NULL, content TEXT NOT NULL)"
    )

    cursor.execute("INSERT INTO users VALUES (1, 'Alice', 'alice@example.com')")
    cursor.execute("INSERT INTO users VALUES (2, 'Bob', 'bob@example.com')")

    cursor.execute("INSERT INTO posts VALUES (1, 1, 'First Post', 'Hello World')")
    cursor.execute("INSERT INTO posts VALUES (2, 1, 'Second Post', 'Another post')")
    cursor.execute("INSERT INTO posts VALUES (3, 2, 'Bob Post', 'Bob content')")

    conn.commit()
    return conn


class TestFetchUserById:
    @pytest.mark.asyncio
    async def test_fetch_existing_user(self):
        conn = create_test_db()
        result = await fetch_user_by_id(conn, 1)
        assert result is not None
        assert result["id"] == 1
        assert result["name"] == "Alice"
        assert result["email"] == "alice@example.com"
        conn.close()

    @pytest.mark.asyncio
    async def test_fetch_nonexistent_user(self):
        conn = create_test_db()
        result = await fetch_user_by_id(conn, 999)
        assert result is None
        conn.close()

    @pytest.mark.asyncio
    async def test_sql_injection_protection(self):
        conn = create_test_db()
        result = await fetch_user_by_id(conn, "1 OR 1=1")
        assert result is None
        conn.close()


class TestFetchUserPosts:
    @pytest.mark.asyncio
    async def test_fetch_user_posts(self):
        conn = create_test_db()
        result = await fetch_user_posts(conn, 1)
        assert len(result) == 2
        assert result[0]["title"] == "First Post"
        assert result[1]["title"] == "Second Post"
        conn.close()

    @pytest.mark.asyncio
    async def test_fetch_user_with_no_posts(self):
        conn = create_test_db()
        result = await fetch_user_posts(conn, 999)
        assert result == []
        conn.close()

    @pytest.mark.asyncio
    async def test_posts_have_correct_structure(self):
        conn = create_test_db()
        result = await fetch_user_posts(conn, 1)
        assert "id" in result[0]
        assert "title" in result[0]
        assert "content" in result[0]
        conn.close()


class TestFetchUserWithPosts:
    @pytest.mark.asyncio
    async def test_fetch_user_with_posts(self):
        conn = create_test_db()
        result = await fetch_user_with_posts(conn, 1)
        assert "user" in result
        assert "posts" in result
        assert result["user"]["name"] == "Alice"
        assert len(result["posts"]) == 2
        conn.close()

    @pytest.mark.asyncio
    async def test_fetch_user_with_posts_structure(self):
        conn = create_test_db()
        result = await fetch_user_with_posts(conn, 1)
        user = result["user"]
        posts = result["posts"]

        assert user["id"] == 1
        assert user["name"] == "Alice"
        assert user["email"] == "alice@example.com"

        assert posts[0]["id"] == 1
        assert posts[0]["title"] == "First Post"
        assert posts[0]["content"] == "Hello World"
        conn.close()

    @pytest.mark.asyncio
    async def test_fetch_nonexistent_user_raises_error(self):
        conn = create_test_db()
        with pytest.raises(ValueError, match="User not found"):
            await fetch_user_with_posts(conn, 999)
        conn.close()

    @pytest.mark.asyncio
    async def test_different_users_different_posts(self):
        conn = create_test_db()
        alice = await fetch_user_with_posts(conn, 1)
        bob = await fetch_user_with_posts(conn, 2)

        assert len(alice["posts"]) == 2
        assert len(bob["posts"]) == 1
        assert bob["posts"][0]["title"] == "Bob Post"
        conn.close()
