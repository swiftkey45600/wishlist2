"""Event durations and selection of owned gifts, including retry and isolation rules."""
import os
from datetime import date, timedelta
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("JWT_SECRET_KEY", "event-experience-tests")
from fastapi.testclient import TestClient
from app.database import get_connection, init_db
from app.main import app
from app.models.event import Event
from app.models.gift import Gift
from app.models.tag import Tag
from app.repositories.event_repository import EventRepository
from app.repositories.gift_repository import GiftRepository
from app.repositories.tag_repository import TagRepository
from app.utils.jwt import create_access_token


class EventExperienceTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.enterContext(patch("app.database.DATABASE_PATH", Path(directory.name) / "db"))
        init_db()
        with get_connection() as conn:
            conn.execute("INSERT INTO users(id,name,login,password_hash) VALUES(2,'Other','other','x')")
        self.client = self.enterContext(TestClient(app))
        self.owner = {"Authorization": "Bearer " + create_access_token({"sub": "johndoe"})}
        self.other = {"Authorization": "Bearer " + create_access_token({"sub": "other"})}
        self.events, self.gifts = EventRepository(), GiftRepository()
        self.source = self.events.create_event(Event(owner_id=1, title="Source"))
        self.target = self.events.create_event(Event(owner_id=1, title="Target"))
        self.url = f"/events/{self.target.id}/gifts/import"

    def wish(self, title="Book", price=100, headers=None):
        return self.client.post("/wishes/", headers=headers or self.owner,
            json={"title": title, "price": price, "tags": ["Книги"], "priority": "high"}).json()

    def test_import_keeps_sources_tags_priority_and_resets_reservation(self):
        wish = self.wish()
        gift = self.gifts.create_gift(Gift(event_id=self.source.id,title="Game",price=200,status="reserved",priority="low"))
        tag = TagRepository().create_tag(Tag(event_id=self.source.id,name="Игры"))
        self.gifts.update_gift(gift.id, {"tag_ids": [tag.id]})
        with get_connection() as conn:
            conn.execute("INSERT INTO reservations(gift_id,reserver_id) VALUES(?,2)", (gift.id,))
        body = {"items": [{"kind":"wish","id":wish["id"]}, {"kind":"gift","id":gift.id}]}
        response = self.client.post(self.url,headers=self.owner,json=body)
        self.assertEqual(response.status_code,200,response.text)
        result = response.json()
        self.assertEqual(result[0]["source_wish_id"], wish["id"])
        self.assertEqual(result[1]["source_gift_id"], gift.id)
        listed = self.client.get(f"/events/{self.target.id}/gifts", headers=self.owner).json()
        self.assertEqual(listed[0]["source_wish_id"], wish["id"])
        self.assertEqual([item["title"] for item in result], ["Book","Game"])
        self.assertEqual([item["priority"] for item in result], ["high","low"])
        self.assertEqual([item["tags"][0]["name"] for item in result], ["Книги","Игры"])
        self.assertTrue(all(item["status"]=="available" and item["reservation_id"] is None for item in result))
        retry = self.client.post(self.url,headers=self.owner,json=body).json()
        self.assertEqual([item["id"] for item in retry], [item["id"] for item in result])
        self.assertEqual(len(self.gifts.get_gifts_by_event(self.target.id)),2)
        self.assertEqual(self.gifts.get_gift_by_id(gift.id).status,"reserved")
        self.assertEqual(len(self.client.get("/wishes/",headers=self.owner).json()),1)
        options = self.client.get(f"/events/{self.target.id}/gift-options",headers=self.owner).json()
        self.assertTrue(all(item["already_added"] for item in options))
        self.assertTrue(all("status" not in item and "owner_id" not in item for item in options))

    def test_foreign_item_rolls_back_whole_batch(self):
        own = self.wish()
        foreign = self.wish("Private",headers=self.other)
        response = self.client.post(self.url,headers=self.owner,json={"items":[{"kind":"wish","id":own["id"]},{"kind":"wish","id":foreign["id"]}]})
        self.assertEqual(response.status_code,404)
        self.assertEqual(self.gifts.get_gifts_by_event(self.target.id),[])
        options = self.client.get(f"/events/{self.target.id}/gift-options",headers=self.owner).json()
        self.assertNotIn("Private",str(options))
        self.assertEqual(self.client.post(self.url,headers=self.other,json={"items":[{"kind":"wish","id":foreign["id"]}]}).status_code,404)
        self.assertIn(self.client.get(f"/events/{self.target.id}/gift-options").status_code,(401,403))

    def test_received_items_archived_target_and_missing_price(self):
        wish = self.wish(price=None)
        body = {"items":[{"kind":"wish","id":wish["id"]}]}
        self.assertEqual(self.client.post(self.url,headers=self.owner,json=body).status_code,422)
        self.client.patch(f"/wishes/{wish['id']}/received",headers=self.owner,json={"received":True})
        self.assertEqual(self.client.get(f"/events/{self.target.id}/gift-options",headers=self.owner).json(),[])
        self.assertEqual(self.client.post(self.url,headers=self.owner,json=body).status_code,404)
        self.events.set_status(self.target.id,1,"archived")
        self.assertEqual(self.client.post(self.url,headers=self.owner,json=body).status_code,409)

    def test_add_from_presents_and_from_event_share_the_same_copy(self):
        wish = self.wish()
        first = self.client.post(f"/wishes/{wish['id']}/events",headers=self.owner,json={"event_id":self.target.id})
        second = self.client.post(self.url,headers=self.owner,json={"items":[{"kind":"wish","id":wish["id"]}]} )
        self.assertEqual(first.json()["gift_id"],second.json()[0]["id"])
        self.assertEqual(len(self.gifts.get_gifts_by_event(self.target.id)),1)

    def test_duration_create_edit_copy_and_change_start(self):
        response = self.client.post("/events/",headers=self.owner,json={"title":"Trip","event_date":"2099-12-31T15:00","duration_days":3})
        self.assertEqual(response.status_code,200,response.text)
        event = response.json()["event"]
        self.assertEqual(event["end_date"],"2100-01-02T23:59:59")
        self.assertEqual(event["duration_days"],3)
        url = f"/events/{event['id']}"
        edited = self.client.patch(url,headers=self.owner,json={"duration_days":7}).json()["event"]
        self.assertEqual(edited["end_date"],"2100-01-06T23:59:59")
        moved = self.client.patch(url,headers=self.owner,json={"event_date":"2100-01-10T11:00"}).json()["event"]
        self.assertEqual(moved["end_date"],"2100-01-16T23:59:59")
        copied = self.client.post(url+"/copy",headers=self.owner,json={"title":"Again","event_date":"2100-02-01T10:00"}).json()["event"]
        self.assertEqual(copied["duration_days"],7)
        self.assertEqual(copied["end_date"],"2100-02-07T23:59:59")
        short = self.client.post(url+"/copy",headers=self.owner,json={"title":"Short","event_date":"2100-02-01","duration_days":2}).json()["event"]
        self.assertEqual(short["end_date"],"2100-02-02T23:59:59")
        cleared = self.client.patch(url,headers=self.owner,json={"event_date":None}).json()["event"]
        self.assertIsNone(cleared["end_date"])
        for days in (0, -1, 3651):
            self.assertEqual(self.client.patch(url,headers=self.owner,json={"duration_days":days}).status_code,422)
        self.assertEqual(self.client.post("/events/",headers=self.owner,json={"title":"No date","duration_days":2}).status_code,422)

    def test_archive_happens_after_last_calendar_day(self):
        today = date.today()
        start = (today-timedelta(days=1)).isoformat()
        event = self.client.post("/events/",headers=self.owner,json={"title":"Two days","event_date":start,"duration_days":2}).json()["event"]
        self.assertEqual(self.events.get_event_by_id(event["id"]).status,"active")
        older = self.client.post("/events/",headers=self.owner,json={"title":"Ended","event_date":(today-timedelta(days=3)).isoformat(),"duration_days":2}).json()["event"]
        self.assertEqual(self.events.get_event_by_id(older["id"]).status,"archived")
