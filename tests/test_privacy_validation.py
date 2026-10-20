import asyncio
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import quote, urlsplit

os.environ.setdefault("JWT_SECRET_KEY", "privacy-validation-test-key")

from app.database import get_connection, init_db
from app.main import app
from app.models.event import Event
from app.models.gift import Gift
from app.models.tag import Tag
from app.repositories.event_repository import EventRepository
from app.repositories.gift_repository import GiftRepository
from app.repositories.tag_repository import TagRepository
from app.utils.jwt import create_access_token


class PrivacyValidationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        database = patch("app.database.DATABASE_PATH", Path(directory.name) / "wishlist.db")
        database.start()
        self.addCleanup(database.stop)
        init_db()
        with get_connection() as connection:
            connection.execute(
                "INSERT INTO users (id, name, login, password_hash) VALUES (2, 'Guest', 'guest', 'unused')"
            )
        self.owner_token = create_access_token({"sub": "johndoe"})
        self.guest_token = create_access_token({"sub": "guest"})
        self.events = EventRepository()
        self.gifts = GiftRepository()
        self.event = self.events.create_event(Event(owner_id=1, title="Private event", public_token="public-token"))
        self.other_event = self.events.create_event(Event(owner_id=2, title="Other event", public_token="other-token"))
        self.gift = self.gifts.create_gift(Gift(event_id=self.event.id, title="Private gift", price=100))

    def request(self, method, path, data=None, token=None):
        body = json.dumps(data).encode() if data is not None else b""
        headers = [(b"content-type", b"application/json")]
        if token is not None:
            headers.append((b"authorization", f"Bearer {token}".encode()))
        url = urlsplit(path)
        scope = {
            "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
            "method": method, "scheme": "http", "path": url.path,
            "query_string": url.query.encode(), "root_path": "", "headers": headers,
            "client": ("127.0.0.1", 12345), "server": ("testserver", 80),
        }
        messages = []

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message):
            messages.append(message)

        asyncio.run(app(scope, receive, send))
        start = next(message for message in messages if message["type"] == "http.response.start")
        content = b"".join(message.get("body", b"") for message in messages if message["type"] == "http.response.body")
        return start["status"], json.loads(content)

    def test_anonymous_requests_cannot_read_by_id(self):
        for path in [f'/events/{self.event.id}', f'/gifts/{self.gift.id}', f'/events/{self.event.id}/gifts', '/events/user/1']:
            with self.subTest(path=path):
                status, payload = self.request("GET", path)
                self.assertIn(status, (401, 403))
                self.assertNotIn("Private", json.dumps(payload))

    def test_other_user_cannot_read_by_id_or_owner_list(self):
        for path in [f'/events/{self.event.id}', f'/gifts/{self.gift.id}', f'/events/{self.event.id}/gifts', '/events/user/1']:
            with self.subTest(path=path):
                status, payload = self.request("GET", path, token=self.guest_token)
                self.assertEqual(status, 403)
                self.assertNotIn("Private", json.dumps(payload))

    def test_owner_can_read_event_gift_and_lists(self):
        status, event = self.request("GET", f'/events/{self.event.id}', token=self.owner_token)
        self.assertEqual(status, 200)
        self.assertEqual(event["event"]["id"], self.event.id)
        status, gift = self.request("GET", f'/gifts/{self.gift.id}', token=self.owner_token)
        self.assertEqual(status, 200)
        self.assertEqual(gift["id"], self.gift.id)
        status, gifts = self.request("GET", f'/events/{self.event.id}/gifts', token=self.owner_token)
        self.assertEqual(status, 200)
        self.assertEqual([gift["id"] for gift in gifts], [self.gift.id])
        for path in ['/events/', '/events/user/1']:
            status, events = self.request("GET", path, token=self.owner_token)
            self.assertEqual(status, 200)
            self.assertEqual([event["id"] for event in events["events"]], [self.event.id])

    def test_missing_event_gift_and_gift_list_return_not_found(self):
        for path in ['/events/999', '/gifts/999', '/events/999/gifts']:
            self.assertEqual(self.request("GET", path, token=self.owner_token)[0], 404)

    def test_public_token_allows_anonymous_and_registered_guests(self):
        for token in [None, self.guest_token]:
            status, payload = self.request("GET", '/events/public/public-token', token=token)
            self.assertEqual(status, 200)
            self.assertEqual(payload["event"]["id"], self.event.id)
            self.assertEqual([gift["id"] for gift in payload["gifts"]], [self.gift.id])
        self.assertEqual(self.request("GET", '/events/public/invalid-token')[0], 404)
        status, payload = self.request("GET", '/events/public/other-token')
        self.assertEqual(status, 200)
        self.assertEqual(payload["gifts"], [])

    def test_filters_and_tags_work_for_owner_and_public_token(self):
        tag = TagRepository().create_tag(Tag(event_id=self.event.id, name="Books"))
        self.gifts.update_gift(self.gift.id, {"tag_ids": [tag.id]})
        self.gifts.create_gift(Gift(event_id=self.event.id, title="Other gift", price=200))
        query = f'?min_price=50&max_price=150&tags={tag.id}&q=PRIVATE&status=available&sort_by=price&sort_order=desc'
        status, gifts = self.request("GET", f'/events/{self.event.id}/gifts{query}', token=self.owner_token)
        self.assertEqual(status, 200)
        self.assertEqual([gift["id"] for gift in gifts], [self.gift.id])
        status, payload = self.request("GET", f'/events/public/public-token{query}')
        self.assertEqual(status, 200)
        self.assertEqual([gift["id"] for gift in payload["gifts"]], [self.gift.id])
        self.assertEqual(payload["gifts"][0]["tags"][0]["id"], tag.id)

    def test_patch_cannot_bypass_gift_privacy(self):
        for data in [{}, {"title": "Changed"}, {"is_reserved": True}, {"is_reserved": False}]:
            with self.subTest(data=data):
                status, payload = self.request("PATCH", f'/gifts/{self.gift.id}', data, token=self.guest_token)
                self.assertEqual(status, 403)
                self.assertNotIn("Private gift", json.dumps(payload))
        self.assertEqual(self.gifts.get_gift_by_id(self.gift.id).title, "Private gift")
        self.assertEqual(self.gifts.get_gift_by_id(self.gift.id).status, "available")
        with get_connection() as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM reservations").fetchone()[0], 0)

    def test_description_search_and_untagged_filter(self):
        tag = TagRepository().create_tag(Tag(event_id=self.event.id, name="Books"))
        self.gifts.update_gift(self.gift.id, {"description": "Красная обложка"})
        tagged = self.gifts.create_gift(Gift(event_id=self.event.id, title="Tagged", price=200), [tag.id])
        for path, token in [(f'/events/{self.event.id}/gifts', self.owner_token), ('/events/public/public-token', None)]:
            status, payload = self.request("GET", path + '?tags=untagged&q=' + quote('ОБЛОЖКА'), token=token)
            self.assertEqual(status, 200)
            gifts = payload if isinstance(payload, list) else payload['gifts']
            self.assertEqual([gift['id'] for gift in gifts], [self.gift.id])
            status, payload = self.request("GET", path + f'?tags=untagged&tags={tag.id}', token=token)
            self.assertEqual(status, 200)
            gifts = payload if isinstance(payload, list) else payload['gifts']
            self.assertEqual({gift['id'] for gift in gifts}, {self.gift.id, tagged.id})

    def test_owner_reservation_details_require_explicit_spoiler_flag(self):
        path = f'/events/public/public-token/gifts/{self.gift.id}/reservation'
        status, gift = self.request("PATCH", path, {"is_reserved": True}, token=self.guest_token)
        self.assertEqual(status, 200)
        reservation_path = f'/reservations/{gift["reservation_id"]}'
        self.assertIn(self.request("GET", reservation_path)[0], (401, 403))
        self.assertEqual(self.request("GET", reservation_path, token=self.owner_token)[0], 403)
        self.assertEqual(self.request("GET", reservation_path, token=self.guest_token)[0], 200)
        for path in [f'/gifts/{self.gift.id}', f'/events/{self.event.id}/gifts', '/events/public/public-token']:
            for suffix, expected in [('', 'available'), ('?status=reserved', 'available'), ('?show_reservations=true', 'reserved')]:
                status, payload = self.request("GET", path + suffix, token=self.owner_token)
                self.assertEqual(status, 200)
                gifts = payload if isinstance(payload, list) else payload.get('gifts', [payload])
                self.assertEqual(len(gifts), 1)
                self.assertEqual(gifts[0]['status'], expected)
                if expected == 'available':
                    self.assertIsNone(gifts[0]['reservation_id'])
        status, payload = self.request("GET", '/events/public/public-token')
        self.assertEqual(payload['gifts'][0]['status'], 'reserved')
        status, gift = self.request("PATCH", f'/gifts/{self.gift.id}', {"description": "Edited"}, token=self.owner_token)
        self.assertEqual(status, 200)
        self.assertEqual(gift['status'], 'available')
        self.assertIsNone(gift['reservation_id'])
        self.assertEqual(self.gifts.get_gift_by_id(self.gift.id).status, 'reserved')

    def test_recommendations_are_owner_only_and_do_not_expose_other_users(self):
        path = f'/events/{self.event.id}/recommendations'
        self.assertIn(self.request("GET", path)[0], (401, 403))
        self.assertEqual(self.request("GET", path, token=self.guest_token)[0], 403)
        self.gifts.create_gift(Gift(event_id=self.other_event.id, title="Secret other user gift", price=100))
        status, items = self.request("GET", path, token=self.owner_token)
        self.assertEqual((status, items), (200, []))
        history = self.events.create_event(Event(owner_id=1, title="History", public_token="history-token"))
        self.gifts.create_gift(Gift(event_id=history.id, title="Private gift", price=100))
        self.gifts.create_gift(Gift(event_id=history.id, title="Candidate", price=150, status="reserved"))
        self.gifts.create_gift(Gift(event_id=history.id, title="Candidate", price=150))
        status, items = self.request("GET", path, token=self.owner_token)
        self.assertEqual(status, 200)
        self.assertEqual([item['title'] for item in items], ['Candidate'])
        for key in ('event_id', 'owner_id', 'public_token', 'reservation_id', 'status', 'tags'):
            self.assertNotIn(key, items[0])
        status, gift = self.request("POST", '/gifts/', {"event_id": self.event.id, **items[0]}, token=self.owner_token)
        self.assertEqual(status, 200)
        self.assertEqual(gift['status'], 'available')
        self.assertIsNone(gift['reservation_id'])
        self.assertEqual(self.request("GET", path, token=self.owner_token)[1], [])

    def test_recommendations_rank_tags_price_and_popularity_and_validate_limit(self):
        history = self.events.create_event(Event(owner_id=1, title="History", public_token="history-token"))
        tags = TagRepository()
        current_tag = tags.create_tag(Tag(event_id=self.event.id, name="Books"))
        history_tag = tags.create_tag(Tag(event_id=history.id, name="Books"))
        self.gifts.update_gift(self.gift.id, {"tag_ids": [current_tag.id]})
        self.gifts.create_gift(Gift(event_id=history.id, title="No matching tag", price=100))
        self.gifts.create_gift(Gift(event_id=history.id, title="Far price", price=1000), [history_tag.id])
        self.gifts.create_gift(Gift(event_id=history.id, title="Rare", price=110), [history_tag.id])
        self.gifts.create_gift(Gift(event_id=history.id, title="Popular", price=110), [history_tag.id])
        self.gifts.create_gift(Gift(event_id=history.id, title="Popular", price=110), [history_tag.id])
        path = f'/events/{self.event.id}/recommendations'
        status, items = self.request("GET", path, token=self.owner_token)
        self.assertEqual(status, 200)
        self.assertEqual([item['title'] for item in items], ['Popular', 'Rare', 'Far price', 'No matching tag'])
        self.assertEqual(len(self.request("GET", path + '?limit=1', token=self.owner_token)[1]), 1)
        for limit in ('0', '21', 'invalid'):
            self.assertEqual(self.request("GET", path + '?limit=' + limit, token=self.owner_token)[0], 422)

    def test_user_list_is_removed_and_own_profile_remains_available(self):
        for token in [None, self.owner_token, self.guest_token]:
            self.assertEqual(self.request("GET", '/users/', token=token)[0], 404)
        self.assertNotIn('/users/', app.openapi()["paths"])
        status, payload = self.request("GET", '/users/me', token=self.owner_token)
        self.assertEqual(status, 200)
        self.assertEqual(payload["user"]["id"], 1)

    def test_registered_guest_can_reserve_and_cancel_with_public_token(self):
        tag = TagRepository().create_tag(Tag(event_id=self.event.id, name="Books"))
        self.gifts.update_gift(self.gift.id, {"tag_ids": [tag.id]})
        path = f'/events/public/public-token/gifts/{self.gift.id}/reservation'
        status, gift = self.request("PATCH", path, {"is_reserved": True}, token=self.guest_token)
        self.assertEqual(status, 200)
        self.assertEqual(gift["id"], self.gift.id)
        self.assertEqual(gift["status"], "reserved")
        self.assertIsNotNone(gift["reservation_id"])
        self.assertEqual(gift["tags"][0]["id"], tag.id)
        with get_connection() as connection:
            reservation = connection.execute("SELECT * FROM reservations WHERE gift_id = ?", (self.gift.id,)).fetchone()
            self.assertEqual(reservation["reserver_id"], 2)
        status, gift = self.request("PATCH", path, {"is_reserved": False}, token=self.guest_token)
        self.assertEqual(status, 200)
        self.assertEqual(gift["status"], "available")
        self.assertIsNone(gift["reservation_id"])
        self.assertEqual(self.request("GET", f'/gifts/{self.gift.id}', token=self.guest_token)[0], 403)

    def test_public_reservation_rejects_wrong_token_and_gift(self):
        for token, gift_id in [('invalid-token', self.gift.id), ('other-token', self.gift.id), ('public-token', 999)]:
            path = f'/events/public/{token}/gifts/{gift_id}/reservation'
            for is_reserved in [True, False]:
                status, payload = self.request("PATCH", path, {"is_reserved": is_reserved}, token=self.guest_token)
                self.assertEqual(status, 404)
                self.assertNotIn("Private gift", json.dumps(payload))
        self.assertEqual(self.gifts.get_gift_by_id(self.gift.id).status, "available")

    def test_public_reservation_requires_jwt_and_rejects_owner(self):
        path = f'/events/public/public-token/gifts/{self.gift.id}/reservation'
        self.assertIn(self.request("PATCH", path, {"is_reserved": True})[0], (401, 403))
        self.assertEqual(self.request("PATCH", path, {"is_reserved": True}, token=self.owner_token)[0], 403)
        self.assertEqual(self.gifts.get_gift_by_id(self.gift.id).status, "available")

    def test_public_reservation_cannot_edit_gift_fields(self):
        path = f'/events/public/public-token/gifts/{self.gift.id}/reservation'
        for data in [{}, {"is_reserved": None}, {"is_reserved": True, "title": "Changed"}, {"is_reserved": True, "price": 1}]:
            self.assertEqual(self.request("PATCH", path, data, token=self.guest_token)[0], 422)
        gift = self.gifts.get_gift_by_id(self.gift.id)
        self.assertEqual(gift.title, "Private gift")
        self.assertEqual(gift.price, 100)
        self.assertEqual(gift.status, "available")

    def test_public_reservation_only_reserver_can_cancel(self):
        path = f'/events/public/public-token/gifts/{self.gift.id}/reservation'
        self.assertEqual(self.request("PATCH", path, {"is_reserved": True}, token=self.guest_token)[0], 200)
        self.assertEqual(self.request("PATCH", path, {"is_reserved": True}, token=self.guest_token)[0], 409)
        with get_connection() as connection:
            connection.execute("INSERT INTO users (id, name, login, password_hash) VALUES (3, 'Other guest', 'other-guest', 'unused')")
        token = create_access_token({"sub": "other-guest"})
        self.assertEqual(self.request("PATCH", path, {"is_reserved": False}, token=token)[0], 403)
        self.assertEqual(self.gifts.get_gift_by_id(self.gift.id).status, "reserved")

    def test_public_reservation_cannot_cancel_secret_word_reservation(self):
        path = f'/events/public/public-token/gifts/{self.gift.id}/reservation'
        self.assertEqual(self.request("POST", path, {"name": "Guest", "secret_word": "snowflake"})[0], 200)
        self.assertEqual(self.request("PATCH", path, {"is_reserved": False}, token=self.guest_token)[0], 403)
        self.assertEqual(self.gifts.get_gift_by_id(self.gift.id).status, "reserved")

    def test_gift_create_rejects_nonpositive_price_and_empty_title(self):
        for field, values in [("price", [0, -1, None]), ("title", ["", " \t\n", None])]:
            for value in values:
                with self.subTest(field=field, value=value):
                    data = {"event_id": self.event.id, "title": "Gift", "price": 100, field: value}
                    self.assertEqual(self.request("POST", '/gifts/', data, token=self.owner_token)[0], 422)
        self.assertEqual(len(self.gifts.get_gifts_by_event(self.event.id)), 1)

    def test_gift_patch_rejects_nonpositive_price_and_empty_title(self):
        for field, values in [("price", [0, -1, None]), ("title", ["", " \t\n", None])]:
            for value in values:
                with self.subTest(field=field, value=value):
                    status, _ = self.request("PATCH", f'/gifts/{self.gift.id}', {field: value}, token=self.owner_token)
                    self.assertEqual(status, 422)
        gift = self.gifts.get_gift_by_id(self.gift.id)
        self.assertEqual(gift.price, 100)
        self.assertEqual(gift.title, "Private gift")

    def test_valid_gift_create_and_patch_preserve_optional_fields_and_tags(self):
        tag = TagRepository().create_tag(Tag(event_id=self.event.id, name="Books"))
        data = {"event_id": self.event.id, "title": "  New gift  ", "price": 1, "description": "Description", "tag_ids": [tag.id]}
        status, gift = self.request("POST", '/gifts/', data, token=self.owner_token)
        self.assertEqual(status, 200)
        self.assertEqual(gift["title"], "New gift")
        self.assertEqual(gift["price"], 1)
        self.assertEqual(gift["description"], "Description")
        self.assertEqual(gift["tags"][0]["id"], tag.id)
        path = f'/gifts/{gift["id"]}'
        status, updated = self.request("PATCH", path, {"title": "  Edited  ", "price": 2}, token=self.owner_token)
        self.assertEqual(status, 200)
        self.assertEqual(updated["title"], "Edited")
        self.assertEqual(updated["price"], 2)
        self.assertEqual(updated["tags"], gift["tags"])
        status, updated = self.request("PATCH", path, {"description": "Updated"}, token=self.owner_token)
        self.assertEqual(status, 200)
        self.assertEqual(updated["title"], "Edited")
        self.assertEqual(updated["price"], 2)

    def test_event_create_and_patch_reject_empty_title(self):
        for title in ["", " \t\n", None]:
            with self.subTest(title=title):
                self.assertEqual(self.request("POST", '/events/', {"title": title}, token=self.owner_token)[0], 422)
                self.assertEqual(self.request("PATCH", f'/events/{self.event.id}', {"title": title}, token=self.owner_token)[0], 422)
        self.assertEqual(self.events.get_event_by_id(self.event.id).title, "Private event")
        self.assertEqual(len(self.events.get_events_by_user(1)), 1)

    def test_valid_event_create_and_partial_patch(self):
        status, payload = self.request("POST", '/events/', {"title": "  Birthday  ", "place": "Home"}, token=self.owner_token)
        self.assertEqual(status, 200)
        event = payload["event"]
        self.assertEqual(event["title"], "Birthday")
        self.assertEqual(event["place"], "Home")
        path = f'/events/{event["id"]}'
        status, payload = self.request("PATCH", path, {"title": "  Party  "}, token=self.owner_token)
        self.assertEqual(status, 200)
        self.assertEqual(payload["event"]["title"], "Party")
        status, payload = self.request("PATCH", path, {"place": "Garden"}, token=self.owner_token)
        self.assertEqual(status, 200)
        self.assertEqual(payload["event"]["title"], "Party")
        self.assertEqual(payload["event"]["place"], "Garden")


if __name__ == "__main__":
    unittest.main()
