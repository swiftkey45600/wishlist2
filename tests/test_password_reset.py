import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

os.environ.setdefault("JWT_SECRET_KEY", "password-reset-test-key")

from fastapi.testclient import TestClient
from app.database import get_connection, init_db
from app.main import app
from app.repositories.auth_mail_rate_limit_repository import AuthMailRateLimitRepository
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.user_repository import UserRepository
from app.routers.auth_router import user_service
from app.services.email_service import EmailDeliveryError
from app.services.password_reset_service import reset_token_hash, RESET_REQUEST_MESSAGE
from app.utils.jwt import create_access_token, verify_token
from app.utils.security import hash_password, verify_password


class PasswordResetTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.path = self.directory / "test.db"
        self.enterContext(patch("app.database.DATABASE_PATH", self.path))
        init_db()
        self.enterContext(patch.dict(os.environ, {
            "SMTP_HOST": "smtp.example.com", "SMTP_USERNAME": "sender@example.com",
            "SMTP_PASSWORD": "smtp-test-password", "SMTP_FROM": "sender@example.com",
            "SMTP_PORT": "465", "SMTP_USE_SSL": "true", "SMTP_TIMEOUT": "10",
            "PUBLIC_API_URL": "https://wishlist.example/api",
        }))
        self.clock = self.enterContext(patch("app.services.password_reset_service.time.time", return_value=1000))
        self.send = self.enterContext(patch("app.services.email_service.EmailService.send"))
        original_hash = hash_password("OriginalPass123")
        with get_connection() as conn:
            conn.execute("UPDATE users SET password_hash = ?, email = 'owner@example.com', email_verified = 1 WHERE id = 1", (original_hash,))
            conn.execute("INSERT INTO users (id, name, login, password_hash, email) VALUES (2, 'Other', 'other', ?, 'unverified@example.com')", (original_hash,))
        self.users = UserRepository()
        self.repo = PasswordResetRepository()
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.owner = {"Authorization": "Bearer " + create_access_token({"user_id": 1, "sub": "johndoe", "auth_version": 0})}
        self.other = {"Authorization": "Bearer " + create_access_token({"user_id": 2, "sub": "other", "auth_version": 0})}
        self.request_path = "/auth/password-reset/request"
        self.confirm_path = "/auth/password-reset/confirm"

    def request(self, email="owner@example.com"):
        return self.client.post(self.request_path, json={"email": email})

    def request_token(self):
        response = self.request()
        self.assertEqual(response.status_code, 202, response.text)
        body = self.send.call_args.args[2]
        link = next(line for line in body.splitlines() if line.startswith("https://"))
        token = parse_qs(urlsplit(link).query)["token"][0]
        self.assertNotIn(token, response.text)
        return token

    def confirm(self, token, password="NewPassword123"):
        return self.client.post(self.confirm_path, json={"token": token, "new_password": password})

    def login(self, password):
        return self.client.post("/auth/login", json={"login": "johndoe", "password": password})

    def test_request_is_generic_and_only_verified_accounts_receive_mail(self):
        responses = []
        for email in ("owner@example.com", "unverified@example.com", "unknown@example.com"):
            responses.append(self.request(email))
        self.assertEqual([response.status_code for response in responses], [202, 202, 202])
        self.assertEqual([response.json() for response in responses], [{"message": RESET_REQUEST_MESSAGE}] * 3)
        self.send.assert_called_once()
        self.assertEqual(self.send.call_args.args[0], "owner@example.com")

    def test_database_has_only_hash_and_password_does_not_change_on_request(self):
        token = self.request_token()
        with get_connection() as conn:
            row = dict(conn.execute("SELECT * FROM password_reset_tokens").fetchone())
        self.assertEqual(row["token_hash"], reset_token_hash(token))
        self.assertNotIn(token, str(row))
        self.assertEqual(row["expires_at"], 2800)
        self.assertEqual(row["auth_version"], 0)
        self.assertEqual(row["activated_at"], 1000)
        self.assertNotIn("OriginalPass123", self.send.call_args.args[2])
        self.assertEqual(self.login("OriginalPass123").status_code, 200)

    def test_reset_changes_hash_consumes_token_and_revokes_all_old_sessions(self):
        legacy_tokens = [create_access_token({"sub": "johndoe"}), create_access_token({"user_id": 1})]
        for token in legacy_tokens:
            self.assertEqual(self.client.get("/users/me", headers={"Authorization": "Bearer " + token}).status_code, 200)
        token = self.request_token()
        response = self.confirm(token)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertNotIn("NewPassword123", response.text)
        self.assertEqual(self.confirm(token).status_code, 400)
        user = self.users.get_user_by_id(1)
        self.assertTrue(verify_password("NewPassword123", user.password))
        self.assertNotEqual(user.password, "NewPassword123")
        self.assertEqual(user.auth_version, 1)
        self.assertTrue(user.email_verified)
        for headers in [self.owner, *({"Authorization": "Bearer " + value} for value in legacy_tokens)]:
            self.assertEqual(self.client.get("/users/me", headers=headers).status_code, 401)
        self.assertEqual(self.client.get("/users/me", headers=self.other).status_code, 200)
        self.assertEqual(self.login("OriginalPass123").status_code, 401)
        fresh = self.login("NewPassword123")
        self.assertEqual(fresh.status_code, 200, fresh.text)
        self.assertEqual(verify_token(fresh.json()["access_token"])["auth_version"], 1)
        self.assertEqual(self.client.get("/users/me", headers={"Authorization": "Bearer " + fresh.json()["access_token"]}).status_code, 200)

    def test_expired_unknown_and_invalid_tokens_do_not_change_password(self):
        token = self.request_token()
        self.clock.return_value = 2800
        for value in (token, "x" * 43):
            self.assertEqual(self.confirm(value).status_code, 400)
        self.assertEqual(self.confirm("short").status_code, 422)
        self.assertTrue(verify_password("OriginalPass123", self.users.get_user_by_id(1).password))

    def test_password_validation_does_not_consume_valid_token(self):
        token = self.request_token()
        for password in ("short", "aaaaaaaa", "я" * 40):
            response = self.confirm(token, password)
            self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self.users.get_user_by_id(1).auth_version, 0)
        self.assertEqual(self.confirm(token).status_code, 200)

    def test_resend_replaces_link_after_cooldown(self):
        old = self.request_token()
        self.clock.return_value += 61
        new = self.request_token()
        self.assertEqual(self.confirm(old).status_code, 400)
        self.assertEqual(self.confirm(new).status_code, 200)

    def test_smtp_failure_has_same_response_and_preserves_previous_link(self):
        token = self.request_token()
        self.clock.return_value += 61
        self.send.side_effect = EmailDeliveryError("private provider details")
        with self.assertLogs("app.services.password_reset_service", level="WARNING") as logs:
            response = self.request()
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json(), {"message": RESET_REQUEST_MESSAGE})
        self.assertNotIn("private provider", str(logs.output))
        self.assertNotIn("owner@example.com", str(logs.output))
        self.assertEqual(self.confirm(token).status_code, 200)

    def test_missing_smtp_fails_equally_for_known_and_unknown(self):
        with patch.dict(os.environ, {"SMTP_PASSWORD": ""}):
            responses = [self.request(email) for email in ("owner@example.com", "unknown@example.com")]
        self.assertEqual([response.status_code for response in responses], [503, 503])
        self.assertEqual(responses[0].json(), responses[1].json())
        self.send.assert_not_called()
        with get_connection() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM password_reset_tokens").fetchone()[0], 0)

    def test_change_email_invalidates_pending_reset_and_resets_verification(self):
        token = self.request_token()
        for email in ("new@example.com", "owner@example.com"):
            response = self.client.patch("/users/me", json={"email": email}, headers=self.owner)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertFalse(response.json()["user"]["email_verified"])
        self.assertEqual(self.confirm(token).status_code, 400)
        self.assertEqual(self.users.get_user_by_id(1).auth_version, 0)

    def test_profile_password_change_revokes_sessions_and_reset_links(self):
        token = self.request_token()
        response = self.client.patch("/users/me", json={"password": "ChangedViaProfile123"}, headers=self.owner)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.users.get_user_by_id(1).auth_version, 1)
        self.assertEqual(self.confirm(token).status_code, 400)
        self.assertEqual(self.client.get("/users/me", headers=self.owner).status_code, 401)
        self.assertEqual(self.login("ChangedViaProfile123").status_code, 200)

    def test_two_concurrent_confirmations_have_one_winner(self):
        token = self.request_token()
        barrier = Barrier(2)
        def confirm(_):
            barrier.wait(timeout=5)
            return self.confirm(token).status_code
        with ThreadPoolExecutor(max_workers=2) as executor:
            statuses = list(executor.map(confirm, range(2)))
        self.assertEqual(sorted(statuses), [200, 400])
        self.assertEqual(self.users.get_user_by_id(1).auth_version, 1)

    def test_email_change_during_delivery_cannot_activate_link(self):
        def change_email(*args):
            self.users.set_email(1, "changed@example.com")
        self.send.side_effect = change_email
        token = self.request_token()
        self.assertEqual(self.confirm(token).status_code, 400)

    def test_password_change_during_delivery_cannot_activate_link(self):
        def change_password(*args):
            user_service.update_user(1, {"password": "ChangedDuringSend123"})
        self.send.side_effect = change_password
        token = self.request_token()
        self.assertEqual(self.confirm(token).status_code, 400)
        self.assertEqual(self.users.get_user_by_id(1).auth_version, 1)

    def test_pending_token_is_not_usable_until_smtp_finishes(self):
        statuses = []
        def during_send(recipient, subject, body):
            link = next(line for line in body.splitlines() if line.startswith("https://"))
            token = parse_qs(urlsplit(link).query)["token"][0]
            statuses.append(self.confirm(token).status_code)
        self.send.side_effect = during_send
        token = self.request_token()
        self.assertEqual(statuses, [400])
        self.assertEqual(self.confirm(token).status_code, 200)

    def test_invalid_token_does_not_trigger_expensive_password_hashing(self):
        with patch("app.services.password_reset_service.hash_password") as hash_function:
            self.assertEqual(self.confirm("x" * 43).status_code, 400)
            hash_function.assert_not_called()

    def test_second_reset_revokes_the_session_issued_after_first_reset(self):
        first = self.request_token()
        self.assertEqual(self.confirm(first).status_code, 200)
        logged_in = self.login("NewPassword123")
        headers = {"Authorization": "Bearer " + logged_in.json()["access_token"]}
        self.assertEqual(self.client.get("/users/me", headers=headers).status_code, 200)
        self.clock.return_value += 61
        second = self.request_token()
        self.assertEqual(self.confirm(second, "AnotherNewPassword123").status_code, 200)
        self.assertEqual(self.users.get_user_by_id(1).auth_version, 2)
        self.assertEqual(self.client.get("/users/me", headers=headers).status_code, 401)
        self.assertEqual(self.login("AnotherNewPassword123").status_code, 200)

    def test_reset_and_verification_tokens_are_not_interchangeable(self):
        token = self.request_token()
        response = self.client.post("/auth/email/verification/confirm", json={"token": token})
        self.assertEqual(response.status_code, 400)
        response = self.client.post("/auth/email/verification/request", headers=self.other)
        self.assertEqual(response.status_code, 202, response.text)
        body = self.send.call_args.args[2]
        link = next(line for line in body.splitlines() if line.startswith("https://"))
        verification_token = parse_qs(urlsplit(link).query)["token"][0]
        self.assertEqual(self.confirm(verification_token).status_code, 400)

    def test_browser_form_get_does_not_consume_token_and_handles_mismatch(self):
        token = self.request_token()
        path = "/auth/password-reset/link"
        response = self.client.get(path, params={"token": token})
        self.assertEqual(response.status_code, 200)
        self.assertIn('type="password"', response.text)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.headers["referrer-policy"], "no-referrer")
        self.assertTrue(self.repo.is_valid(reset_token_hash(token), 1000))
        response = self.client.post(path, data={"token": token, "new_password": "NewPassword123", "new_password_repeat": "DifferentPassword"})
        self.assertEqual(response.status_code, 422)
        self.assertNotIn("NewPassword123", response.text)
        self.assertTrue(self.repo.is_valid(reset_token_hash(token), 1000))
        response = self.client.post(path, data={"token": token, "new_password": "NewPassword123", "new_password_repeat": "NewPassword123"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(token, response.text)
        self.assertEqual(self.login("NewPassword123").status_code, 200)
        self.assertEqual(self.client.post(path, data={"token": token, "new_password": "NewPassword123", "new_password_repeat": "NewPassword123"}).status_code, 400)

    def test_browser_form_preserves_api_prefix(self):
        token = self.request_token()
        with TestClient(app, root_path="/api", base_url="https://wishlist.example") as client:
            response = client.get("/api/auth/password-reset/link", params={"token": token})
        self.assertIn('action="/api/auth/password-reset/link"', response.text)

    def test_rate_limit_is_same_for_known_unknown_and_unverified_addresses(self):
        for email in ("owner@example.com", "unknown@example.com", "unverified@example.com"):
            first = self.request(email)
            second = self.request(email)
            self.assertEqual(first.status_code, 202)
            self.assertEqual(second.status_code, 429)
            self.assertEqual(second.headers["retry-after"], "60")
        self.clock.return_value = 1060
        self.assertEqual(self.request("owner@example.com").status_code, 202)

    def test_email_hour_limit_and_persistence_after_init(self):
        for number in range(5):
            self.clock.return_value = 1000 + 61 * number
            self.assertEqual(self.request().status_code, 202)
        init_db()
        self.clock.return_value += 61
        response = self.request()
        self.assertEqual(response.status_code, 429)
        self.assertGreater(int(response.headers["retry-after"]), 60)
        self.clock.return_value = 4600
        self.assertEqual(self.request().status_code, 202)

    def test_ip_limit_cannot_be_bypassed_by_changing_email(self):
        for number in range(20):
            self.assertEqual(self.request(f"missing{number}@example.com").status_code, 202)
        response = self.request("missing-last@example.com")
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["retry-after"], "3600")
        self.send.assert_not_called()

    def test_limits_are_shared_with_verification_and_are_atomic(self):
        response = self.client.post("/auth/email/verification/request", headers=self.other)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(self.request("unverified@example.com").status_code, 429)
        barrier = Barrier(2)
        def request(_):
            barrier.wait(timeout=5)
            return self.request("race@example.com").status_code
        with ThreadPoolExecutor(max_workers=2) as executor:
            statuses = list(executor.map(request, range(2)))
        self.assertEqual(sorted(statuses), [202, 429])

    def test_verification_user_limit_cannot_be_bypassed_by_changing_email(self):
        self.assertEqual(self.client.post("/auth/email/verification/request", headers=self.other).status_code, 202)
        self.client.post("/users/me/email", json={"email": "changed-unverified@example.com"}, headers=self.other)
        response = self.client.post("/auth/email/verification/request", headers=self.other)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["retry-after"], "60")

    def test_deleted_account_cascades_tokens(self):
        token = self.request_token()
        self.users.delete_user(1)
        self.assertEqual(self.confirm(token).status_code, 400)
        with get_connection() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM password_reset_tokens").fetchone()[0], 0)

    def test_newer_successful_delivery_wins_even_if_old_smtp_finishes_later(self):
        old, new = "a" * 43, "b" * 43
        self.assertTrue(self.repo.create_pending("owner@example.com", reset_token_hash(old), 1000, 1800))
        self.assertTrue(self.repo.create_pending("owner@example.com", reset_token_hash(new), 1000, 1800))
        self.assertTrue(self.repo.activate(reset_token_hash(new), 1001))
        self.assertFalse(self.repo.activate(reset_token_hash(old), 1002))
        self.assertEqual(self.confirm(old).status_code, 400)
        self.assertEqual(self.confirm(new).status_code, 200)

    def test_old_password_login_racing_with_reset_cannot_get_new_session_version(self):
        old_user = self.users.get_user_by_id(1)
        token = self.request_token()
        self.confirm(token)
        with patch.object(user_service, "authenticate_user", return_value=old_user):
            response = self.login("OriginalPass123")
        stale_token = response.json()["access_token"]
        self.assertEqual(verify_token(stale_token)["auth_version"], 0)
        self.assertEqual(self.client.get("/users/me", headers={"Authorization": "Bearer " + stale_token}).status_code, 401)

    def test_registration_accepts_optional_email_and_never_trusts_verified_flag(self):
        response = self.client.post("/auth/register", json={
            "name": "New", "login": "new-user", "password": "NewPass123", "email": "NewUser@EXAMPLE.COM", "email_verified": True,
        })
        self.assertEqual(response.status_code, 200, response.text)
        headers = {"Authorization": "Bearer " + response.json()["access_token"]}
        self.assertEqual(self.client.get("/users/me/email", headers=headers).json(), {"email": "newuser@example.com", "email_verified": False})
        response = self.client.post("/auth/register", json={"name": "Other", "login": "another", "password": "NewPass123", "email": "NEWUSER@example.com"})
        self.assertEqual(response.status_code, 400)

    def test_invalid_session_versions_are_not_accepted(self):
        for version in (True, False, "0", None, -1, 1):
            token = create_access_token({"user_id": 1, "auth_version": version})
            self.assertEqual(self.client.get("/users/me", headers={"Authorization": "Bearer " + token}).status_code, 401)

    def test_old_database_gets_version_zero_without_losing_email_or_password(self):
        legacy = self.directory / "legacy.db"
        conn = sqlite3.connect(legacy)
        try:
            conn.executescript("""CREATE TABLE users (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL, login TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL, birthday TEXT, gender INTEGER,
                email TEXT COLLATE NOCASE, email_verified INTEGER NOT NULL DEFAULT 0);
                INSERT INTO users (id, name, login, password_hash, email, email_verified)
                VALUES (1, 'Old', 'johndoe', 'original-hash', 'owner@example.com', 1);""")
            conn.commit()
        finally:
            conn.close()
        with patch("app.database.DATABASE_PATH", legacy):
            init_db()
            init_db()
            user = self.users.get_user_by_id(1)
            self.assertEqual(user.auth_version, 0)
            self.assertEqual(user.password, "original-hash")
            self.assertTrue(user.email_verified)
            self.assertEqual(self.client.get("/users/me", headers=self.owner).status_code, 200)


if __name__ == "__main__":
    unittest.main()
