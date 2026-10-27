import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

os.environ.setdefault("JWT_SECRET_KEY", "email-verification-test-key")

from fastapi.testclient import TestClient
from app.config import get_public_api_url, SMTPConfigurationError
from app.database import get_connection, init_db
from app.main import app
from app.repositories.user_repository import UserRepository
from app.routers.email_verification_router import service
from app.services.email_service import EmailDeliveryError
from app.services.email_verification_service import verification_token_hash
from app.utils.jwt import create_access_token


class EmailVerificationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "test.db"
        self.enterContext(patch("app.database.DATABASE_PATH", self.path))
        init_db()
        self.enterContext(patch.dict(os.environ, {
            "SMTP_HOST": "smtp.example.com", "SMTP_USERNAME": "sender@example.com",
            "SMTP_PASSWORD": "test-mail-password", "SMTP_FROM": "sender@example.com",
            "SMTP_PORT": "465", "SMTP_USE_SSL": "true", "SMTP_TIMEOUT": "10",
            "PUBLIC_API_URL": "https://wishlist.example/api",
        }))
        self.send = self.enterContext(patch("app.services.email_service.EmailService.send"))
        self.clock = self.enterContext(patch("app.services.email_verification_service.time.time", return_value=1000))
        with get_connection() as conn:
            conn.execute("INSERT INTO users (id, name, login, password_hash) VALUES (2, 'Other', 'other', 'unused')")
        self.users = UserRepository()
        self.users.set_email(1, "kirill@example.com")
        self.users.set_email(2, "other@example.com")
        self.owner = {"Authorization": "Bearer " + create_access_token({"user_id": 1, "sub": "johndoe"})}
        self.other = {"Authorization": "Bearer " + create_access_token({"user_id": 2, "sub": "other"})}
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.request_path = "/auth/email/verification/request"
        self.confirm_path = "/auth/email/verification/confirm"

    def request_token(self, headers=None):
        response = self.client.post(self.request_path, headers=headers or self.owner)
        self.assertEqual(response.status_code, 202, response.text)
        recipient, subject, body = self.send.call_args.args
        link = next(line for line in body.splitlines() if line.startswith("https://"))
        token = parse_qs(urlsplit(link).query)["token"][0]
        self.assertNotIn(token, response.text)
        return token, link

    def confirm(self, token):
        return self.client.post(self.confirm_path, json={"token": token})

    def test_request_sends_link_and_database_contains_only_hash(self):
        token, link = self.request_token()
        self.assertEqual(len(token), 43)
        self.assertTrue(link.startswith("https://wishlist.example/api/auth/email/verification/link?"))
        self.assertEqual(self.send.call_args.args[0], "kirill@example.com")
        with get_connection() as conn:
            row = dict(conn.execute("SELECT * FROM email_verification_tokens").fetchone())
        self.assertEqual(row["token_hash"], verification_token_hash(token))
        self.assertNotIn(token, str(row))
        self.assertEqual(row["expires_at"], 2800)
        self.assertEqual(row["activated_at"], 1000)
        self.assertIsNone(row["used_at"])
        self.assertFalse(self.users.get_user_by_id(1).email_verified)

    def test_confirm_without_login_once_and_status_in_own_profile(self):
        token, _ = self.request_token()
        self.assertEqual(self.confirm(token).status_code, 200)
        self.assertEqual(self.confirm(token).status_code, 400)
        self.assertTrue(self.users.get_user_by_login("johndoe").email_verified)
        self.assertFalse(self.users.get_user_by_id(2).email_verified)
        for path in ("/users/me", "/users/me/email"):
            response = self.client.get(path, headers=self.owner)
            payload = response.json().get("user", response.json())
            self.assertTrue(payload["email_verified"])
        forbidden = self.client.get("/users/1", headers=self.other)
        self.assertEqual(forbidden.status_code, 403)
        self.assertNotIn("email_verified", forbidden.text)
        self.assertNotIn("kirill@example.com", forbidden.text)
        self.assertEqual(self.client.get("/events/", headers=self.owner).status_code, 200)

    def test_request_requires_auth_and_only_uses_current_users_email(self):
        self.assertIn(self.client.post(self.request_path).status_code, (401, 403))
        self.send.assert_not_called()
        token, _ = self.request_token(self.other)
        self.assertEqual(self.send.call_args.args[0], "other@example.com")
        self.assertEqual(self.confirm(token).status_code, 200)
        self.assertFalse(self.users.get_user_by_id(1).email_verified)
        self.assertTrue(self.users.get_user_by_id(2).email_verified)

    def test_missing_email_and_already_verified_do_not_send(self):
        with get_connection() as conn:
            conn.execute("UPDATE users SET email = NULL WHERE id = 1")
        self.assertEqual(self.client.post(self.request_path, headers=self.owner).status_code, 409)
        self.send.assert_not_called()
        self.users.set_email(1, "kirill@example.com")
        token, _ = self.request_token()
        self.confirm(token)
        self.send.reset_mock()
        self.assertEqual(self.client.post(self.request_path, headers=self.owner).status_code, 409)
        self.send.assert_not_called()

    def test_expired_unknown_and_malformed_tokens(self):
        token, _ = self.request_token()
        self.clock.return_value = 2800
        self.assertEqual(self.confirm(token).status_code, 400)
        self.assertEqual(self.confirm("x" * 43).status_code, 400)
        self.assertEqual(self.confirm("short").status_code, 422)
        self.assertEqual(self.client.post(self.confirm_path, json={}).status_code, 422)
        self.assertFalse(self.users.get_user_by_id(1).email_verified)

    def test_resend_success_replaces_previous_link(self):
        old, _ = self.request_token()
        self.clock.return_value += 61
        new, _ = self.request_token()
        self.assertNotEqual(old, new)
        self.assertEqual(self.confirm(old).status_code, 400)
        self.assertEqual(self.confirm(new).status_code, 200)

    def test_failure_does_not_claim_delivery_or_invalidate_existing_link(self):
        old, _ = self.request_token()
        self.send.side_effect = EmailDeliveryError("private provider details")
        self.clock.return_value += 61
        response = self.client.post(self.request_path, headers=self.owner)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private provider", response.text)
        with get_connection() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM email_verification_tokens").fetchone()[0], 1)
        self.assertEqual(self.confirm(old).status_code, 200)

    def test_unconfigured_smtp_does_not_issue_token(self):
        with patch.dict(os.environ, {"SMTP_PASSWORD": ""}):
            response = self.client.post(self.request_path, headers=self.owner)
        self.assertEqual(response.status_code, 503)
        self.send.assert_not_called()
        with get_connection() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM email_verification_tokens").fetchone()[0], 0)

    def test_email_change_and_change_back_invalidate_old_links(self):
        token, _ = self.request_token()
        for email in ("new@example.com", "kirill@example.com"):
            response = self.client.post("/users/me/email", json={"email": email}, headers=self.owner)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.json()["email_verified"])
        self.assertEqual(self.confirm(token).status_code, 400)
        self.clock.return_value += 61
        token, _ = self.request_token()
        self.assertEqual(self.confirm(token).status_code, 200)
        # Re-saving the same normalized address preserves confirmation.
        response = self.client.post("/users/me/email", json={"email": "KIRILL@EXAMPLE.COM"}, headers=self.owner)
        self.assertTrue(response.json()["email_verified"])
        response = self.client.post("/users/me/email", json={"email": "different@example.com"}, headers=self.owner)
        self.assertFalse(response.json()["email_verified"])

    def test_email_changed_during_send_cannot_be_confirmed(self):
        self.send.side_effect = lambda *args: self.users.set_email(1, "changed@example.com")
        response = self.client.post(self.request_path, headers=self.owner)
        self.assertEqual(response.status_code, 409)
        body = self.send.call_args.args[2]
        link = next(line for line in body.splitlines() if line.startswith("https://"))
        token = parse_qs(urlsplit(link).query)["token"][0]
        self.assertEqual(self.confirm(token).status_code, 400)
        self.assertFalse(self.users.get_user_by_id(1).email_verified)

    def test_token_cannot_be_used_before_delivery_finishes(self):
        statuses = []
        def during_send(recipient, subject, body):
            link = next(line for line in body.splitlines() if line.startswith("https://"))
            token = parse_qs(urlsplit(link).query)["token"][0]
            statuses.append(self.confirm(token).status_code)
        self.send.side_effect = during_send
        token, _ = self.request_token()
        self.assertEqual(statuses, [400])
        self.assertEqual(self.confirm(token).status_code, 200)

    def test_newer_successful_send_wins_if_smtp_completes_out_of_order(self):
        repo = service.repository
        old, new = "a" * 43, "b" * 43
        repo.create_pending(1, verification_token_hash(old), 1000, 1800)
        repo.create_pending(1, verification_token_hash(new), 1000, 1800)
        self.assertTrue(repo.activate(verification_token_hash(new), 1001))
        self.assertFalse(repo.activate(verification_token_hash(old), 1002))
        self.assertEqual(self.confirm(old).status_code, 400)
        self.assertEqual(self.confirm(new).status_code, 200)

    def test_two_confirmations_have_one_winner(self):
        token, _ = self.request_token()
        barrier = Barrier(2)
        def confirm(_):
            barrier.wait(timeout=5)
            return self.confirm(token).status_code
        with ThreadPoolExecutor(max_workers=2) as executor:
            statuses = list(executor.map(confirm, range(2)))
        self.assertEqual(sorted(statuses), [200, 400])

    def test_browser_link_requires_explicit_post_and_has_no_external_resources(self):
        token, _ = self.request_token()
        path = "/auth/email/verification/link"
        response = self.client.get(path, params={"token": token})
        self.assertEqual(response.status_code, 200)
        self.assertIn('method="post"', response.text)
        self.assertIn('lang="ru"', response.text)
        self.assertEqual(response.headers["referrer-policy"], "no-referrer")
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertIn("default-src 'none'", response.headers["content-security-policy"])
        self.assertFalse(self.users.get_user_by_id(1).email_verified)
        response = self.client.post(path, data={"token": token})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(token, response.text)
        self.assertTrue(self.users.get_user_by_id(1).email_verified)

    def test_browser_form_uses_external_api_prefix(self):
        token, _ = self.request_token()
        with TestClient(app, root_path="/api", base_url="https://wishlist.example") as client:
            response = client.get("/api/auth/email/verification/link", params={"token": token})
            self.assertEqual(response.status_code, 200)
            self.assertIn('action="/api/auth/email/verification/link"', response.text)
            response = client.post("/api/auth/email/verification/link", data={"token": token})
            self.assertEqual(response.status_code, 200, response.text)

    def test_deleted_account_invalidates_link(self):
        token, _ = self.request_token()
        self.users.delete_user(1)
        self.assertEqual(self.confirm(token).status_code, 400)
        with get_connection() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM email_verification_tokens").fetchone()[0], 0)

    def test_link_origin_is_configured_not_from_host_header(self):
        response = self.client.post(self.request_path, headers={**self.owner, "Host": "evil.example"})
        self.assertEqual(response.status_code, 202)
        body = self.send.call_args.args[2]
        self.assertIn("https://wishlist.example/api/", body)
        self.assertNotIn("evil.example", body)

    def test_public_api_url_validation(self):
        for value in ("http://evil.example", "https://user:pass@example.com", "https://example.com/?a=b", "https://example.com/#fragment", "javascript:alert(1)"):
            with self.subTest(value=value), patch.dict(os.environ, {"PUBLIC_API_URL": value}):
                with self.assertRaises(SMTPConfigurationError):
                    get_public_api_url()
        with patch.dict(os.environ, {"PUBLIC_API_URL": "http://127.0.0.1:8000/"}):
            self.assertEqual(get_public_api_url(), "http://127.0.0.1:8000")

    def test_migration_preserves_old_email_without_trusting_it(self):
        legacy = self.path.with_name("legacy.db")
        schema = Path("app/schema.sql").read_text().replace(
            ",\n    email_verified INTEGER NOT NULL DEFAULT 0 CHECK (email_verified IN (0, 1))", ""
        )
        with sqlite3.connect(legacy) as conn:
            conn.executescript(schema)
            conn.execute("UPDATE users SET email = 'legacy@example.com' WHERE id = 1")
        conn.close()
        with patch("app.database.DATABASE_PATH", legacy):
            init_db()
            init_db()
            user = self.users.get_user_by_id(1)
            self.assertEqual(user.email, "legacy@example.com")
            self.assertFalse(user.email_verified)
            token, _ = self.request_token()
            self.assertEqual(self.confirm(token).status_code, 200)


if __name__ == "__main__":
    unittest.main()
