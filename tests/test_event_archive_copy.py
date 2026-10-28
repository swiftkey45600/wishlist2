"""S8.2: event lifecycle, transactional copying and archived reservation guards."""
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Event as ThreadEvent
from unittest.mock import patch

os.environ.setdefault("JWT_SECRET_KEY", "event-lifecycle-test-key")

from fastapi.testclient import TestClient
from app.database import get_connection, init_db
from app.main import app
from app.models.event import Event
from app.models.gift import Gift
from app.models.reservation import Reservation
from app.models.tag import Tag
from app.models.contribution import Contribution
from app.repositories.contribution_repository import ContributionRepository
from app.repositories.event_repository import EventRepository
from app.repositories.gift_repository import GiftRepository
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.tag_repository import TagRepository
from app.utils.jwt import create_access_token


class EventLifecycleTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.directory = Path(folder.name)
        database = patch("app.database.DATABASE_PATH", self.directory / "test.db")
        database.start()
        self.addCleanup(database.stop)
        init_db()
        with get_connection() as conn:
            conn.execute("INSERT INTO users (id, name, login, password_hash) VALUES (2, 'Guest', 'guest', 'unused')")
        self.events = EventRepository()
        self.gifts = GiftRepository()
        self.reservations = ReservationRepository()
        self.event = self.events.create_event(Event(
            owner_id=1, title="Birthday", description="Description", place="Home",
            event_date="2026-01-01", public_token="original-token",
        ))
        self.gift = self.gifts.create_gift(Gift(event_id=self.event.id, title="Book", price=500))
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.owner = {"Authorization": "Bearer " + create_access_token({"user_id": 1, "sub": "johndoe"})}
        self.guest = {"Authorization": "Bearer " + create_access_token({"user_id": 2, "sub": "guest"})}

    def archive(self):
        response = self.client.patch(f"/events/{self.event.id}/archive", headers=self.owner)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["event"]

    def copy(self, **data):
        return self.client.post(f"/events/{self.event.id}/copy", headers=self.owner, json={"title": "Next birthday", **data})

    def test_archive_restore_is_idempotent_and_public_status_is_visible(self):
        for _ in range(2):
            event = self.archive()
            self.assertEqual(event["status"], "archived")
            self.assertEqual(event["public_token"], self.event.public_token)
        public = self.client.get("/events/public/original-token")
        self.assertEqual(public.status_code, 200, public.text)
        self.assertEqual(public.json()["event"]["status"], "archived")
        self.assertEqual(len(public.json()["gifts"]), 1)
        self.assertEqual(self.client.get(f"/events/{self.event.id}", headers=self.owner).json()["event"]["status"], "archived")
        for _ in range(2):
            response = self.client.patch(f"/events/{self.event.id}/restore", headers=self.owner)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["event"]["status"], "active")

    def test_lists_support_status_and_default_remains_backward_compatible(self):
        active = self.events.create_event(Event(owner_id=1, title="Active"))
        self.events.create_event(Event(owner_id=2, title="Not mine", status="archived"))
        self.archive()
        for prefix in ("/events/", "/events/user/1"):
            for state, expected in (("active", [active.id]), ("archived", [self.event.id])):
                result = self.client.get(prefix, params={"status": state}, headers=self.owner)
                self.assertEqual(result.status_code, 200)
                self.assertEqual([event["id"] for event in result.json()["events"]], expected)
            all_events = self.client.get(prefix, headers=self.owner).json()["events"]
            self.assertEqual({event["id"] for event in all_events}, {active.id, self.event.id})
        self.assertEqual(self.client.get("/events/?status=unknown", headers=self.owner).status_code, 422)
        self.events.set_status(active.id, 1, "archived")
        self.assertEqual(self.client.get("/events/user/1?status=active", headers=self.owner).json(), {"events": []})

    def test_invalid_event_ids_are_rejected_before_database_access(self):
        for event_id in ("0", "-1", "9223372036854775808"):
            for action in ("archive", "restore", "copy"):
                with self.subTest(event_id=event_id, action=action):
                    url = f"/events/{event_id}/{action}"
                    response = (self.client.post(url, json={"title": "Copy"}, headers=self.owner)
                                if action == "copy" else self.client.patch(url, headers=self.owner))
                    self.assertEqual(response.status_code, 422)

    def test_only_owner_can_archive_restore_and_copy(self):
        for action, method in (("archive", "patch"), ("restore", "patch"), ("copy", "post")):
            request = getattr(self.client, method)
            kwargs = {"json": {"title": "Copy"}} if action == "copy" else {}
            with self.subTest(action=action):
                path = f"/events/{self.event.id}/{action}"
                self.assertIn(request(path, **kwargs).status_code, (401, 403))
                self.assertEqual(request(path, headers=self.guest, **kwargs).status_code, 403)
                self.assertEqual(request(f"/events/999999/{action}", headers=self.owner, **kwargs).status_code, 404)
        self.assertEqual(self.events.get_event_by_id(self.event.id).status, "active")
        self.assertEqual(len(self.events.get_events_by_user(1)), 1)

    def test_archived_events_block_all_new_reservation_endpoints(self):
        self.archive()
        cases = (
            ("POST", "/reservations/", {"gift_id": self.gift.id, "is_anonymous": False, "public_token": self.event.public_token}, self.guest),
            ("POST", f"/events/public/original-token/gifts/{self.gift.id}/reservation", {"name": "Guest", "secret_word": "snowflake"}, {}),
            ("PATCH", f"/events/public/original-token/gifts/{self.gift.id}/reservation", {"is_reserved": True}, self.guest),
            ("PATCH", f"/gifts/{self.gift.id}", {"is_reserved": True}, self.guest),
        )
        for method, path, body, headers in cases:
            with self.subTest(path=path):
                response = self.client.request(method, path, json=body, headers=headers)
                # The private gift PATCH can reject guests before attempting a reservation.
                self.assertIn(response.status_code, (403, 409), response.text)
        self.assertIsNone(self.reservations.get_reservation_by_gift(self.gift.id))
        self.assertEqual(self.gifts.get_gift_by_id(self.gift.id).status, "available")
        self.client.patch(f"/events/{self.event.id}/restore", headers=self.owner)
        response = self.client.post("/reservations/", json={"gift_id": self.gift.id, "is_anonymous": False, "public_token": self.event.public_token}, headers=self.guest)
        self.assertEqual(response.status_code, 200, response.text)

    def test_guest_can_cancel_existing_reservation_in_archive(self):
        path = f"/events/public/original-token/gifts/{self.gift.id}/reservation"
        response = self.client.post(path, json={"name": "Guest", "secret_word": "snowflake"})
        self.assertEqual(response.status_code, 200, response.text)
        self.archive()
        self.assertIsNotNone(self.reservations.get_reservation_by_gift(self.gift.id))
        response = self.client.request("DELETE", path, json={"secret_word": "snowflake"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.events.get_event_by_id(self.event.id).status, "archived")

    def test_registered_guest_can_cancel_existing_reservation_in_archive(self):
        reservation = self.reservations.reserve_gift(Reservation(gift_id=self.gift.id, is_anonymous=False, reserver_id=2))
        self.archive()
        response = self.client.delete(f"/reservations/{reservation.id}", headers=self.guest)
        self.assertEqual(response.status_code, 200, response.text)

    def test_contributions_blocked_in_archive_but_existing_can_be_cancelled(self):
        gift = self.gifts.create_gift(Gift(event_id=self.event.id, title="Laptop", price=1000, contribution_goal=1000))
        path = f"/events/public/original-token/gifts/{gift.id}/contributions"
        response = self.client.post(path, headers=self.guest, json={"amount": 1000})
        self.assertEqual(response.status_code, 200, response.text)
        contribution_id = response.json()["id"]
        self.archive()
        # Existing funded state survives archiving.
        self.assertEqual(self.gifts.get_gift_by_id(gift.id).contribution_total, 1000)
        response = self.client.delete(f"{path}/{contribution_id}", headers=self.guest)
        self.assertEqual(response.status_code, 200, response.text)
        for headers, data in ((self.guest, {"amount": 100}), ({}, {"amount": 100, "name": "Guest", "secret_word": "snowflake"})):
            response = self.client.post(path, headers=headers, json=data)
            self.assertEqual(response.status_code, 409, response.text)
        self.client.patch(f"/events/{self.event.id}/restore", headers=self.owner)
        self.assertEqual(self.client.post(path, headers=self.guest, json={"amount": 100}).status_code, 200)

    def test_copy_has_independent_gifts_tags_and_no_reservations_or_contributions(self):
        tags = TagRepository()
        used = tags.create_tag(Tag(event_id=self.event.id, name="Books"))
        tags.create_tag(Tag(event_id=self.event.id, name="Unused tag"))
        self.gifts.update_gift(self.gift.id, {"tag_ids": [used.id], "share_in_recommendations": True})
        self.reservations.reserve_gift(Reservation(gift_id=self.gift.id, is_anonymous=False, reserver_id=2))
        fundraising = self.gifts.create_gift(Gift(
            event_id=self.event.id, title="Laptop", price=1000, contribution_goal=1000,
            marketplace_url="https://example.com/item", picture_url="https://example.com/picture.jpg",
            description="Model A",
        ), [used.id])
        ContributionRepository().create_contribution(Contribution(gift_id=fundraising.id, amount=1000, contributor_id=2, is_anonymous=False))
        self.gifts.create_gift(Gift(event_id=self.event.id, title="Bought", price=None, status="bought"))
        self.archive()
        response = self.copy(event_date="2027-05-10")
        self.assertEqual(response.status_code, 201, response.text)
        copied = response.json()["event"]
        self.assertEqual(copied["status"], "active")
        self.assertNotEqual(copied["id"], self.event.id)
        self.assertNotEqual(copied["public_token"], self.event.public_token)
        self.assertEqual(copied["event_date"], "2027-05-10")
        self.assertEqual(copied["description"], self.event.description)
        self.assertEqual(copied["place"], self.event.place)
        new_gifts = self.gifts.get_gifts_by_event(copied["id"])
        new_tags = tags.get_tags_by_event(copied["id"])
        self.assertEqual({tag.name for tag in new_tags}, {"Books", "Unused tag"})
        self.assertTrue({tag.id for tag in new_tags}.isdisjoint({tag.id for tag in tags.get_tags_by_event(self.event.id)}))
        self.assertTrue({gift.id for gift in new_gifts}.isdisjoint({self.gift.id, fundraising.id}))
        self.assertEqual(len(new_gifts), 3)
        for gift in new_gifts:
            self.assertEqual(gift.status, "available")
            self.assertIsNone(gift.reservation_id)
            self.assertEqual(gift.contribution_total, 0)
            self.assertFalse(gift.share_in_recommendations)
            self.assertEqual(ContributionRepository().get_contributions_by_gift(gift.id), [])
            for tag in gift.tags:
                self.assertEqual(tag.event_id, copied["id"])
        laptop = next(gift for gift in new_gifts if gift.title == "Laptop")
        self.assertEqual(laptop.contribution_goal, 1000)
        self.assertEqual(laptop.marketplace_url, fundraising.marketplace_url)
        self.assertEqual(laptop.picture_url, fundraising.picture_url)
        self.gifts.update_gift(laptop.id, {"title": "Changed copy"})
        tags.update_tag(Tag(id=new_tags[0].id, event_id=copied["id"], name="Changed tag"))
        self.assertEqual(self.gifts.get_gift_by_id(fundraising.id).title, "Laptop")
        self.assertEqual(tags.get_tags_by_event(self.event.id)[0].name, "Books")
        self.assertEqual(self.events.get_event_by_id(self.event.id).status, "archived")
        self.assertIsNotNone(self.reservations.get_reservation_by_gift(self.gift.id))
        self.assertEqual(self.gifts.get_gift_by_id(fundraising.id).contribution_total, 1000)

    def test_copy_resets_old_date_and_accepts_empty_event(self):
        response = self.copy()
        self.assertIsNone(response.json()["event"]["event_date"])
        self.assertNotEqual(response.json()["event"]["public_token"], self.copy().json()["event"]["public_token"])
        empty = self.events.create_event(Event(owner_id=1, title="Empty"))
        response = self.client.post(f"/events/{empty.id}/copy", json={"title": "New"}, headers=self.owner)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.gifts.get_gifts_by_event(response.json()["event"]["id"]), [])

    def test_copy_preserves_cover_and_gift_priorities(self):
        with get_connection() as conn:
            image_id = conn.execute(
                "INSERT INTO images (image_path, image_type, hash, owner_id) VALUES ('cover.png', 'image/png', 'cover-hash', 1)"
            ).lastrowid
            conn.execute("UPDATE events SET cover_image_id = ? WHERE id = ?", (image_id, self.event.id))
        self.gifts.update_gift(self.gift.id, {"priority": "high"})
        self.gifts.create_gift(Gift(event_id=self.event.id, title="Low priority", price=100, priority="low"))
        response = self.copy()
        self.assertEqual(response.status_code, 201, response.text)
        event = response.json()["event"]
        self.assertEqual(event["cover_image_id"], image_id)
        self.assertEqual(
            {gift.title: gift.priority for gift in self.gifts.get_gifts_by_event(event["id"])},
            {"Book": "high", "Low priority": "low"},
        )

    def test_copy_validates_title_and_date(self):
        for data in ({}, {"title": " "}, {"title": None}, {"title": "New", "event_date": "2027-02-30"}):
            response = self.client.post(f"/events/{self.event.id}/copy", json=data, headers=self.owner)
            self.assertEqual(response.status_code, 422, response.text)
        response = self.copy(title="  Trimmed  ", event_date=None)
        self.assertEqual(response.json()["event"]["title"], "Trimmed")
        self.assertEqual(len(self.events.get_events_by_user(1)), 2)
        response = self.copy(event_date="2027-05-10T18:30")
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["event"]["event_date"], "2027-05-10T18:30:00")

    def test_copy_failure_rolls_back_event_gifts_and_tags(self):
        tag = TagRepository().create_tag(Tag(event_id=self.event.id, name="Books"))
        self.gifts.update_gift(self.gift.id, {"tag_ids": [tag.id]})
        self.gifts.create_gift(Gift(event_id=self.event.id, title="Fail", price=100))
        with get_connection() as conn:
            counts = [conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in ("events", "gifts", "tags", "gift_tags")]
            conn.execute("""CREATE TRIGGER copy_failure BEFORE INSERT ON gifts WHEN NEW.title = 'Fail'
                            BEGIN SELECT RAISE(ABORT, 'injected copy failure'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            self.events.copy_event(self.event.id, 1, "Copy", None)
        with get_connection() as conn:
            after = [conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in ("events", "gifts", "tags", "gift_tags")]
        self.assertEqual(after, counts)

    def test_image_survives_source_event_deletion_and_cannot_be_deleted_while_used(self):
        path = self.directory / "image.png"
        path.write_bytes(b"image bytes")
        with get_connection() as conn:
            image_id = conn.execute(
                "INSERT INTO images (image_path, image_type, hash, owner_id) VALUES (?, 'image/png', 'image-hash', 1)", (str(path),)
            ).lastrowid
            conn.execute("UPDATE gifts SET image_id = ? WHERE id = ?", (image_id, self.gift.id))
        copied_id = self.copy().json()["event"]["id"]
        copied_gift = self.gifts.get_gifts_by_event(copied_id)[0]
        self.assertEqual(copied_gift.image_id, image_id)
        self.assertEqual(self.client.delete(f"/images/{image_id}", headers=self.owner).status_code, 409)
        self.client.delete(f"/events/{self.event.id}", headers=self.owner)
        self.assertEqual(self.client.get(f"/images/{image_id}").status_code, 200)
        self.assertEqual(self.client.delete(f"/images/{image_id}", headers=self.owner).status_code, 409)
        self.gifts.update_gift(copied_gift.id, {"image_id": None})
        self.assertEqual(self.client.delete(f"/images/{image_id}", headers=self.owner).status_code, 200)
        self.assertFalse(path.exists())

    def test_reservation_repositories_recheck_archive_inside_transaction(self):
        self.archive()
        for reserve in (
            lambda: self.reservations.reserve_gift(Reservation(gift_id=self.gift.id, is_anonymous=False, reserver_id=2)),
            lambda: self.reservations.reserve_guest_gift(Reservation(gift_id=self.gift.id, is_anonymous=False), "secret-hash"),
        ):
            with self.assertRaises(sqlite3.IntegrityError):
                reserve()
        self.assertIsNone(self.reservations.get_reservation_by_gift(self.gift.id))

    def test_concurrent_reservation_waits_for_archive_and_is_rejected(self):
        started = ThreadEvent()
        def reserve():
            started.set()
            return self.reservations.reserve_gift(Reservation(gift_id=self.gift.id, is_anonymous=False, reserver_id=2))
        with ThreadPoolExecutor(max_workers=1) as executor:
            with get_connection() as conn:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute("UPDATE events SET status = 'archived' WHERE id = ?", (self.event.id,))
                future = executor.submit(reserve)
                self.assertTrue(started.wait(timeout=2))
            with self.assertRaises(sqlite3.IntegrityError):
                future.result(timeout=5)
        self.assertEqual(self.gifts.get_gift_by_id(self.gift.id).status, "available")

    def test_old_database_migration_is_repeatable_and_preserves_events(self):
        old_path = self.directory / "legacy.db"
        schema = Path("app/schema.sql").read_text().replace(
            "    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived')),\n", ""
        )
        with sqlite3.connect(old_path) as conn:
            conn.executescript(schema)
            conn.execute("INSERT INTO events (owner_id, title, public_token) VALUES (1, 'Old event', 'old-token')")
        conn.close()
        with patch("app.database.DATABASE_PATH", old_path):
            init_db()
            init_db()
            old = self.events.get_event_by_id(1)
            self.assertEqual(old.status, "active")
            self.assertEqual(old.public_token, "old-token")
            with get_connection() as conn:
                with self.assertRaises(sqlite3.IntegrityError):
                    conn.execute("UPDATE events SET status = 'invalid' WHERE id = 1")


if __name__ == "__main__":
    unittest.main()
