"""Receiving gifts and carrying wishes from completed events."""
from datetime import date, timedelta
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
os.environ.setdefault('JWT_SECRET_KEY', 'lifecycle-test-key')
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


class GiftLifecycleTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        database = patch('app.database.DATABASE_PATH', Path(folder.name) / 'test.db')
        database.start()
        self.addCleanup(database.stop)
        init_db()
        with get_connection() as db:
            db.execute("INSERT INTO users (id,name,login,password_hash) VALUES (2,'Guest','guest','unused')")
        self.events, self.gifts, self.tags = EventRepository(), GiftRepository(), TagRepository()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        self.old = self.events.create_event(Event(owner_id=1,title='Past',event_date=yesterday,public_token='old-token'))
        self.new = self.events.create_event(Event(owner_id=1,title='Next',public_token='new-token'))
        tag = self.tags.create_tag(Tag(event_id=self.old.id,name='Книги'))
        self.gift = self.gifts.create_gift(Gift(event_id=self.old.id,title='Book',price=100), [tag.id])
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.owner = {'Authorization': 'Bearer ' + create_access_token({'sub':'johndoe'})}
        self.guest = {'Authorization': 'Bearer ' + create_access_token({'sub':'guest'})}

    def test_old_event_archived_and_today_event_active(self):
        today = self.events.create_event(Event(owner_id=1,title='Today',event_date=date.today().isoformat()))
        result = self.client.get('/events/', headers=self.owner).json()['events']
        statuses = {event['id']: event['status'] for event in result}
        self.assertEqual(statuses[self.old.id], 'archived')
        self.assertEqual(statuses[today.id], 'active')
        self.assertEqual(self.client.get('/events/public/old-token').json()['event']['status'], 'archived')

    def test_multiday_event_archives_after_last_day(self):
        start = (date.today() - timedelta(days=1)).isoformat() + 'T10:00'
        end = (date.today() + timedelta(days=1)).isoformat() + 'T18:00'
        created = self.client.post('/events/',headers=self.owner,json={'title':'Trip','event_date':start,'end_date':end})
        self.assertEqual(created.status_code,200,created.text)
        event = created.json()['event']
        self.assertEqual(self.client.get(f'/events/{event["id"]}',headers=self.owner).json()['event']['status'],'active')
        invalid = self.client.post('/events/',headers=self.owner,json={'title':'Bad','event_date':end,'end_date':start})
        self.assertEqual(invalid.status_code,422)

    def test_expired_event_needs_new_date_before_restore(self):
        result = self.client.patch(f'/events/{self.old.id}/restore', headers=self.owner)
        self.assertEqual(result.status_code, 409)
        changed = self.client.patch(f'/events/{self.old.id}', headers=self.owner, json={'event_date':date.today().isoformat()})
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(self.client.patch(f'/events/{self.old.id}/restore', headers=self.owner).json()['event']['status'], 'active')

    def test_owner_marks_received_and_restores_without_deleting(self):
        url = f'/gifts/{self.gift.id}/received'
        self.assertEqual(self.client.patch(url, headers=self.guest, json={'received':True}).status_code, 404)
        self.assertTrue(self.client.patch(url, headers=self.owner, json={'received':True}).json()['received'])
        self.assertEqual(self.client.get('/events/public/old-token').json()['gifts'], [])
        self.assertFalse(self.client.patch(url, headers=self.owner, json={'received':False}).json()['received'])
        self.assertEqual(len(self.client.get('/events/public/old-token').json()['gifts']), 1)

    def test_carry_preserves_original_reservation_and_maps_tags(self):
        with get_connection() as db:
            db.execute("UPDATE gifts SET status='reserved' WHERE id=?", (self.gift.id,))
            db.execute('INSERT INTO reservations (gift_id,reserver_id) VALUES (?,2)', (self.gift.id,))
        url = f'/gifts/{self.gift.id}/carry'
        self.assertEqual(self.client.post(url, headers=self.guest, json={'event_id':self.new.id}).status_code, 409)
        result = self.client.post(url, headers=self.owner, json={'event_id':self.new.id})
        self.assertEqual(result.status_code, 200, result.text)
        copied = result.json()
        self.assertEqual(copied['title'], 'Book')
        self.assertEqual(copied['status'], 'available')
        self.assertEqual([tag['name'] for tag in copied['tags']], ['Книги'])
        self.assertNotEqual(copied['tags'][0]['event_id'], self.old.id)
        original = self.gifts.get_gift_by_id(self.gift.id)
        self.assertTrue(original.carried_forward)
        self.assertEqual(original.status, 'reserved')
        self.assertIsNotNone(original.reservation_id)
        self.assertEqual(self.client.post(url, headers=self.owner, json={'event_id':self.new.id}).status_code, 409)

    def test_received_gift_cannot_be_carried(self):
        self.client.patch(f'/gifts/{self.gift.id}/received', headers=self.owner, json={'received':True})
        self.assertEqual(self.client.post(f'/gifts/{self.gift.id}/carry', headers=self.owner, json={'event_id':self.new.id}).status_code, 409)
