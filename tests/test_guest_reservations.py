import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("JWT_SECRET_KEY", "guest-reservation-test-key")

from app.database import get_connection, init_db
from app.main import app
from app.models.event import Event
from app.models.gift import Gift
from app.repositories.event_repository import EventRepository
from app.repositories.gift_repository import GiftRepository
from app.repositories.reservation_repository import ReservationRepository
from app.utils.jwt import create_access_token
from app.utils.security import verify_password


class GuestReservationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        database = patch("app.database.DATABASE_PATH", Path(directory.name) / "wishlist.db")
        database.start()
        self.addCleanup(database.stop)
        init_db()
        self.event = EventRepository().create_event(Event(owner_id=1, title="Birthday", public_token="test-token"))
        self.gift = GiftRepository().create_gift(Gift(event_id=self.event.id, title="Book", price=100))
        self.path = f"/events/public/{self.event.public_token}/gifts/{self.gift.id}/reservation"
        self.repo = ReservationRepository()

    def request(self, method, path=None, data=None, client_ip="127.0.0.1", token=None):
        body = json.dumps(data).encode() if data is not None else b""
        headers = [(b"content-type", b"application/json")]
        if token is not None:
            headers.append((b"authorization", f"Bearer {token}".encode()))
        scope = {
            "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
            "method": method, "scheme": "http", "path": path or self.path,
            "query_string": b"", "root_path": "", "headers": headers,
            "client": (client_ip, 12345), "server": ("testserver", 80),
        }
        messages = []

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message):
            messages.append(message)

        asyncio.run(app(scope, receive, send))
        start = next(message for message in messages if message["type"] == "http.response.start")
        content = b"".join(message.get("body", b"") for message in messages if message["type"] == "http.response.body")
        return start["status"], json.loads(content), dict(start["headers"])

    def reserve(self, secret_word="snowflake", **kwargs):
        return self.request("POST", data={"name": "  Guest  ", "secret_word": secret_word}, **kwargs)

    def test_guest_can_reserve_and_cancel_without_jwt(self):
        status, reservation, _ = self.reserve()
        self.assertEqual(status, 200)
        self.assertEqual(reservation["reserver_name"], "Guest")
        self.assertIsNone(reservation["reserver_id"])
        self.assertEqual(GiftRepository().get_gift_by_id(self.gift.id).status, "reserved")
        status, _, _ = self.request("DELETE", data={"secret_word": "snowflake"})
        self.assertEqual(status, 200)
        self.assertIsNone(self.repo.get_reservation_by_gift(self.gift.id))
        self.assertEqual(GiftRepository().get_gift_by_id(self.gift.id).status, "available")

    def test_only_hash_is_stored_and_never_returned(self):
        _, reservation, _ = self.reserve()
        hashed = self.repo.get_secret_word_hash(reservation["id"])
        self.assertNotEqual(hashed, "snowflake")
        self.assertTrue(verify_password("snowflake", hashed))
        owner_token = create_access_token({"sub": "johndoe"})
        self.assertIn(self.request("GET", path=f'/reservations/{reservation["id"]}')[0], (401, 403))
        for path, token in [
            (f'/gifts/{self.gift.id}', owner_token),
            ('/events/public/test-token', None),
        ]:
            status, payload, _ = self.request("GET", path=path, token=token)
            self.assertEqual(status, 200)
            serialized = json.dumps(payload)
            self.assertNotIn("secret_word", serialized)
            self.assertNotIn(hashed, serialized)
            self.assertNotIn("snowflake", serialized)

    def test_wrong_word_does_not_cancel_reservation(self):
        self.reserve()
        status, _, _ = self.request("DELETE", data={"secret_word": "wrong"})
        self.assertEqual(status, 403)
        self.assertIsNotNone(self.repo.get_reservation_by_gift(self.gift.id))
        self.assertEqual(GiftRepository().get_gift_by_id(self.gift.id).status, "reserved")

    def test_duplicate_and_bought_gifts_cannot_be_reserved(self):
        self.assertEqual(self.reserve()[0], 200)
        self.assertEqual(self.reserve()[0], 409)
        bought = GiftRepository().create_gift(Gift(event_id=self.event.id, title="Bought", price=10, status="bought"))
        path = f'/events/public/test-token/gifts/{bought.id}/reservation'
        self.assertEqual(self.reserve(path=path)[0], 409)
        self.assertIsNone(self.repo.get_reservation_by_gift(bought.id))

    def test_public_token_must_match_gift_event(self):
        other = EventRepository().create_event(Event(owner_id=1, title="Other", public_token="other-token"))
        for token in [other.public_token, "invalid-token"]:
            path = f'/events/public/{token}/gifts/{self.gift.id}/reservation'
            self.assertEqual(self.reserve(path=path)[0], 404)
            self.assertEqual(self.request("DELETE", path=path, data={"secret_word": "snowflake"})[0], 404)
        self.assertIsNone(self.repo.get_reservation_by_gift(self.gift.id))

    def test_validation_rejects_empty_and_oversized_input(self):
        for name, word in [(" ", "valid"), ("x" * 101, "valid"), ("Guest", " "), ("Guest", "я" * 37)]:
            with self.subTest(name=name, word=word):
                status, _, _ = self.request("POST", data={"name": name, "secret_word": word})
                self.assertEqual(status, 422)
        self.assertEqual(self.request("DELETE", data={"secret_word": "я" * 37})[0], 422)
        self.assertEqual(self.request("POST", data={"name": "Guest"})[0], 422)

    def test_word_is_case_sensitive_and_supports_unicode(self):
        self.assertEqual(self.reserve(secret_word="Снежинка")[0], 200)
        self.assertEqual(self.request("DELETE", data={"secret_word": "снежинка"})[0], 403)
        self.assertEqual(self.request("DELETE", data={"secret_word": "Снежинка"})[0], 200)

    def test_registered_reservation_cannot_be_cancelled_by_word(self):
        token = create_access_token({"sub": "johndoe"})
        status, reservation, _ = self.request(
            "POST", path="/reservations/", data={"gift_id": self.gift.id, "is_anonymous": False}, token=token
        )
        self.assertEqual(status, 200)
        self.assertEqual(self.request("DELETE", data={"secret_word": "snowflake"})[0], 403)
        self.assertEqual(self.request("DELETE", path=f'/reservations/{reservation["id"]}', token=token)[0], 200)

    def test_registered_user_cannot_cancel_guest_reservation(self):
        _, reservation, _ = self.reserve()
        token = create_access_token({"sub": "johndoe"})
        self.assertEqual(self.request("DELETE", path=f'/reservations/{reservation["id"]}', token=token)[0], 403)
        self.assertIsNotNone(self.repo.get_reservation_by_gift(self.gift.id))

    def test_cancel_keeps_bought_status(self):
        self.reserve()
        GiftRepository().update_gift_status(self.gift.id, "bought")
        self.assertEqual(self.request("DELETE", data={"secret_word": "snowflake"})[0], 200)
        self.assertEqual(GiftRepository().get_gift_by_id(self.gift.id).status, "bought")

    def test_cancellation_rate_limit_survives_new_repository_and_expires(self):
        self.reserve()
        with patch("app.repositories.reservation_repository.time.time", return_value=1000):
            for _ in range(5):
                self.assertEqual(self.request("DELETE", data={"secret_word": "wrong"})[0], 403)
            self.assertEqual(ReservationRepository().check_guest_rate_limit("127.0.0.1", self.gift.id), 60)
            status, _, headers = self.request("DELETE", data={"secret_word": "snowflake"})
            self.assertEqual(status, 429)
            self.assertEqual(headers[b"retry-after"], b"60")
        with patch("app.repositories.reservation_repository.time.time", return_value=1060):
            self.assertEqual(self.request("DELETE", data={"secret_word": "snowflake"})[0], 200)

    def test_cancellation_limit_cannot_be_bypassed_by_changing_ip(self):
        self.reserve()
        for index in range(5):
            self.assertEqual(self.request("DELETE", data={"secret_word": "wrong"}, client_ip=f"192.0.2.{index}")[0], 403)
        self.assertEqual(self.request("DELETE", data={"secret_word": "snowflake"}, client_ip="192.0.2.100")[0], 429)

    def test_cancellation_ip_limit_applies_across_gifts(self):
        for index in range(5):
            gift = GiftRepository().create_gift(Gift(event_id=self.event.id, title=f"Gift {index}", price=100))
            path = f'/events/public/test-token/gifts/{gift.id}/reservation'
            self.assertEqual(self.request("DELETE", path=path, data={"secret_word": "wrong"})[0], 404)
        self.assertEqual(self.request("DELETE", data={"secret_word": "wrong"})[0], 429)

    def test_invalid_public_token_cannot_lock_guest_reservation(self):
        self.reserve()
        path = f'/events/public/invalid-token/gifts/{self.gift.id}/reservation'
        for _ in range(6):
            self.assertEqual(self.request("DELETE", path=path, data={"secret_word": "wrong"})[0], 404)
        self.assertEqual(self.request("DELETE", data={"secret_word": "snowflake"})[0], 200)

    def test_creation_limit_is_atomic_under_concurrent_requests(self):
        with ThreadPoolExecutor(max_workers=12) as executor:
            results = list(executor.map(lambda _: ReservationRepository().check_guest_rate_limit("192.0.2.1"), range(12)))
        self.assertEqual(results.count(None), 10)
        self.assertEqual(sum(value is not None for value in results), 2)

    def test_creation_endpoint_returns_rate_limit_and_retry_after(self):
        self.assertEqual(self.reserve()[0], 200)
        for _ in range(9):
            self.assertEqual(self.reserve()[0], 409)
        status, _, headers = self.reserve()
        self.assertEqual(status, 429)
        self.assertGreater(int(headers[b"retry-after"]), 0)
        self.assertEqual(self.reserve(client_ip="192.0.2.50")[0], 409)

    def test_concurrent_reservations_have_one_winner(self):
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: self.reserve()[0], range(2)))
        self.assertEqual(sorted(results), [200, 409])
        with get_connection() as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM reservations").fetchone()[0], 1)
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_migration_preserves_existing_reservations(self):
        with get_connection() as connection:
            connection.execute("DROP TABLE reservations")
            connection.execute(
                "CREATE TABLE reservations (id INTEGER PRIMARY KEY, gift_id INTEGER UNIQUE, reserver_name TEXT, "
                "reserver_id INTEGER, is_anonymous INTEGER NOT NULL DEFAULT 0)"
            )
            connection.execute("INSERT INTO reservations (gift_id, reserver_id) VALUES (?, 1)", (self.gift.id,))
        init_db()
        init_db()
        reservation = self.repo.get_reservation_by_gift(self.gift.id)
        self.assertEqual(reservation.reserver_id, 1)
        self.assertIsNone(self.repo.get_secret_word_hash(reservation.id))


if __name__ == "__main__":
    unittest.main()
