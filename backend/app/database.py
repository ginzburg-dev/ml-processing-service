import sqlite3
from pathlib import Path
from typing import Optional, Tuple

import structlog
from passlib.hash import bcrypt

from backend.app.config import MLServiceConfig
from backend.app.password import hash_password, verify_password

LOGGER = structlog.get_logger()

class UserDatabase():
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

        with self._sql_connect() as connect:
            connect.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user'
                )
            """)
            connect.commit()

    def _sql_connect(self):
        return sqlite3.connect(self.db_path)

    def create_user(
            self,
            username: str,
            password: str,
            role: str = "user"
    ) -> None:
        password_hash = hash_password(password)
        try:
            with self._sql_connect() as connect:
                connect.execute(
                    "INSERT INTO users(username, password_hash, role) VALUES(?,?,?)",
                    (username, password_hash, role),
                )
                connect.commit()
                LOGGER.info("User created", username=username, role=role)

        except sqlite3.IntegrityError:
            LOGGER.warning("User already exists", username=username)
            raise ValueError(f"User '{username}' already exists")

    def verify_user(self, username: str, password: str) -> Optional[Tuple[int, str, str]]:
        """
        Returns (id, username, role) if ok, else None.
        """
        with self._sql_connect() as con:
            row = con.execute(
                "SELECT id, username, password_hash, role FROM users WHERE username=?",
                (username,),
            ).fetchone()

        if not row:
            return None

        user_id, uname, password_hash, role = row
        if verify_password(password, password_hash):
            return (user_id, uname, role)
        return None

    def list_users(self) -> list[Tuple[int, str, str]]:
        with self._sql_connect() as connect:
            rows = connect.execute("SELECT id, username, role FROM users ORDER BY username").fetchall()
        return [(int(user[0]), str(user[1]), str(user[2])) for user in rows]

    def get_user_by_id(self, user_id: int) -> Optional[Tuple[int, str, str]]:
        with self._sql_connect() as connect:
            row = connect.execute("SELECT id, username, role FROM users WHERE id=?", (user_id,)).fetchone()
        if not row:
            return None
        return (int(row[0]), str(row[1]), str(row[2]))

    def set_username(self, user_id: int, new_username: str) -> None:
        with self._sql_connect() as connect:
            connect.execute("UPDATE users SET username=? WHERE id=?", (new_username, user_id))
            connect.commit()
            LOGGER.info("Set username", user_id=user_id, username=new_username)

    def set_role(self, user_id: int, new_role: str) -> None:
        with self._sql_connect() as connect:
            connect.execute("UPDATE users SET role=? WHERE id=?", (new_role, user_id))
            connect.commit()
            LOGGER.info("Set role", user_id=user_id, role=new_role)

    def set_password(self, user_id: int, new_password: str) -> None:
        pw_hash = hash_password(new_password)
        with self._sql_connect() as connect:
            connect.execute("UPDATE users SET password_hash=? WHERE id=?", (pw_hash, user_id))
            connect.commit()
            LOGGER.info("Set password", user_id=user_id)

    def delete_user(self, user_id: int) -> None:
        with self._sql_connect() as connect:
            connect.execute("DELETE FROM users WHERE id=?", (user_id,))
            connect.commit()
            LOGGER.info("Delete user", user_id=user_id)
