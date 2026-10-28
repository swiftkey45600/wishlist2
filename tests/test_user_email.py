"""Email storage only: no verification, recovery or email delivery."""
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

os.environ.setdefault("JWT_SECRET_KEY", "user-email-test-key")

from fastapi.testclient import TestClient
from app.database import get_connection, init_db
from app.main import app
from app.repositories.user_repository import UserRepository
from app.utils.jwt import create_access_token


class UserEmailTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "test.db"
        database = patch("app.database.DATABASE_PATH", self.path)
        database.start()
        self.addCleanup(database.stop)
        init_db()
        with get_connection() as conn:
            conn.execute("INSERT INTO users (id, name, login, password_hash) VALUES (2, 'Other', 'other', 'unused')")
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.owner = {"Authorization": "Bearer " + create_access_token({"user_id": 1, "sub": "johndoe"})}
        self.other = {"Authorization": "Bearer " + create_access_token({"user_id": 2, "sub": "other"})}
        self.url = "/users/me/email"

    def save(self, email, headers=None):
        return self.client.post(self.url, json={"email": email}, headers=headers or self.owner)

    def test_existing_users_have_null_email_and_require_authentication(self):
        response = self.client.get(self.url, headers=self.owner)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"email": None, "email_verified": False})
        self.assertIn(self.client.get(self.url).status_code, (401, 403))
        self.assertIn(self.client.post(self.url, json={"email": "a@example.com"}).status_code, (401, 403))
        self.assertEqual(self.client.get(self.url, headers={"Authorization": "Bearer invalid"}).status_code, 401)

    def test_save_read_replace_and_repeat(self):
        response = self.save("  Kirill@EXAMPLE.COM  ")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {"email": "kirill@example.com", "email_verified": False})
        self.assertEqual(self.client.get(self.url, headers=self.owner).json(), response.json())
        self.assertEqual(UserRepository().get_user_by_id(1).email, "kirill@example.com")
        self.assertEqual(UserRepository().get_user_by_login("johndoe").email, "kirill@example.com")
        self.assertEqual(self.save("KIRILL@example.com").status_code, 200)
        self.assertEqual(self.save("new@example.com").json(), {"email": "new@example.com", "email_verified": False})
        # Replaced address becomes available to another account.
        self.assertEqual(self.save("kirill@example.com", self.other).status_code, 200)

    def test_unique_email_conflict_preserves_both_users(self):
        self.save("first@example.com")
        self.save("second@example.com", self.other)
        response = self.save("FIRST@EXAMPLE.COM", self.other)
        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(self.client.get(self.url, headers=self.owner).json(), {"email": "first@example.com", "email_verified": False})
        self.assertEqual(self.client.get(self.url, headers=self.other).json(), {"email": "second@example.com", "email_verified": False})

    def test_invalid_email_does_not_change_stored_address(self):
        self.save("valid@example.com")
        for email in (None, "", " ", "not-an-email", "a@", "@example.com", "a@example..com", "a\r\nBcc:b@example.com", "x" * 255 + "@example.com"):
            with self.subTest(email=email):
                self.assertEqual(self.save(email).status_code, 422)
        self.assertEqual(self.client.post(self.url, json={}, headers=self.owner).status_code, 422)
        self.assertEqual(self.client.get(self.url, headers=self.owner).json(), {"email": "valid@example.com", "email_verified": False})

    def test_profile_can_clear_email_without_storing_none_string(self):
        self.assertEqual(self.save("valid@example.com").status_code, 200)
        response = self.client.patch("/users/me", json={"email": None}, headers=self.owner)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["user"]["email"])
        self.assertIsNone(UserRepository().get_user_by_id(1).email)
        self.assertEqual(self.client.patch("/users/me", json={"email": None}, headers=self.other).status_code, 200)

    def test_email_is_private_and_cannot_be_set_for_another_user(self):
        self.save("private@example.com")
        response = self.client.get("/users/1", headers=self.other)
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("private@example.com", response.text)
        self.assertEqual(self.client.get(self.url, headers=self.other).json(), {"email": None, "email_verified": False})
        response = self.client.post(self.url, json={"email": "stolen@example.com", "user_id": 1}, headers=self.other)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.client.get(self.url, headers=self.owner).json(), {"email": "private@example.com", "email_verified": False})

    def test_own_profile_contains_email_without_secrets(self):
        self.save("profile@example.com")
        response = self.client.get("/users/me", headers=self.owner)
        self.assertEqual(response.json()["user"]["email"], "profile@example.com")
        self.assertNotIn("password", response.json()["user"])
        response = self.client.patch("/users/me", json={"name": "New name"}, headers=self.owner)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["user"]["email"], "profile@example.com")

    def test_email_persists_after_reinitialization_without_session_revocation(self):
        self.save("persist@example.com")
        init_db()
        init_db()
        self.assertEqual(self.client.get(self.url, headers=self.owner).json(), {"email": "persist@example.com", "email_verified": False})
        self.assertEqual(self.client.get("/events/", headers=self.owner).status_code, 200)

    def test_registration_and_login_still_work_without_email(self):
        data = {"name": "Legacy", "login": "legacy-user", "password": "LegacyPass123"}
        response = self.client.post("/auth/register", json=data)
        self.assertEqual(response.status_code, 200, response.text)
        headers = {"Authorization": "Bearer " + response.json()["access_token"]}
        self.assertEqual(self.client.get(self.url, headers=headers).json(), {"email": None, "email_verified": False})
        self.client.post(self.url, json={"email": "legacy@example.com"}, headers=headers)
        response = self.client.post("/auth/login", json={"login": data["login"], "password": data["password"]})
        self.assertEqual(response.status_code, 200, response.text)
        headers = {"Authorization": "Bearer " + response.json()["access_token"]}
        self.assertEqual(self.client.get(self.url, headers=headers).json(), {"email": "legacy@example.com", "email_verified": False})

    def test_database_enforces_unique_addresses_but_allows_multiple_nulls(self):
        self.save("unique@example.com")
        with get_connection() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE users SET email = 'UNIQUE@EXAMPLE.COM' WHERE id = 2")
        self.assertIsNone(UserRepository().get_user_by_id(2).email)

    def test_concurrent_claim_of_email_has_one_winner(self):
        barrier = Barrier(2)
        def claim(headers):
            barrier.wait(timeout=5)
            return self.save("same@example.com", headers).status_code
        with ThreadPoolExecutor(max_workers=2) as executor:
            statuses = list(executor.map(claim, (self.owner, self.other)))
        self.assertEqual(sorted(statuses), [200, 409])
        with get_connection() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM users WHERE email = 'same@example.com'").fetchone()[0], 1)

    def test_migration_from_database_without_email_preserves_accounts(self):
        legacy = self.path.with_name("legacy.db")
        schema = Path("app/schema.sql").read_text().replace("    gender INTEGER,\n    email TEXT COLLATE NOCASE,\n    email_verified INTEGER NOT NULL DEFAULT 0 CHECK (email_verified IN (0, 1))", "    gender INTEGER")
        connection = sqlite3.connect(legacy)
        try:
            connection.executescript(schema)
            connection.execute("UPDATE users SET password_hash = 'original-hash' WHERE id = 1")
            connection.commit()
        finally:
            connection.close()
        with patch("app.database.DATABASE_PATH", legacy):
            init_db()
            init_db()
            user = UserRepository().get_user_by_id(1)
            self.assertEqual(user.password, "original-hash")
            self.assertEqual(user.login, "johndoe")
            self.assertIsNone(user.email)
            # A token for a different password hash must not authenticate against
            # the migrated database, even when user ID and auth_version match.
            self.assertEqual(self.client.get(self.url, headers=self.owner).status_code, 401)
            headers = {"Authorization": "Bearer " + create_access_token({"user_id": 1, "sub": "johndoe"})}
            self.assertEqual(self.save("migrated@example.com", headers=headers).status_code, 200)


if __name__ == "__main__":
    unittest.main()
