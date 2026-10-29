"""Personal wishes survive event deletion and can be added to an event."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.database import get_connection, init_db
from app.main import app
from app.models.event import Event
from app.models.contribution import Contribution
from app.models.gift import Gift
from app.models.tag import Tag
from app.repositories.contribution_repository import ContributionRepository
from app.repositories.event_repository import EventRepository
from app.repositories.gift_repository import GiftRepository
from app.repositories.tag_repository import TagRepository
from app.utils.jwt import create_access_token

class PersonalWishTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        database = patch('app.database.DATABASE_PATH', Path(folder.name) / 'db.sqlite')
        database.start()
        self.addCleanup(database.stop)
        init_db()
        with get_connection() as db:
            db.execute("INSERT INTO users (id,name,login,password_hash) VALUES (2,'Other','other','x')")
        self.events, self.gifts = EventRepository(), GiftRepository()
        self.event = self.events.create_event(Event(owner_id=1,title='Event'))
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.owner = {'Authorization': 'Bearer ' + create_access_token({'sub':'johndoe'})}
        self.other = {'Authorization': 'Bearer ' + create_access_token({'sub':'other'})}

    def test_create_edit_and_add_copy_to_owned_event(self):
        response = self.client.post('/wishes/', headers=self.owner, json={'title':'Book','price':100,'tags':['Книги']})
        self.assertEqual(response.status_code, 201, response.text)
        wish_id = response.json()['id']
        self.assertEqual(self.client.get('/wishes/',headers=self.other).json(), [])
        self.assertEqual(self.client.put(f'/wishes/{wish_id}',headers=self.other,json={'title':'Stolen'}).status_code,404)
        self.assertEqual(self.client.post(f'/wishes/{wish_id}/events',headers=self.other,json={'event_id':self.event.id}).status_code,404)
        added = self.client.post(f'/wishes/{wish_id}/events',headers=self.owner,json={'event_id':self.event.id})
        self.assertEqual(added.status_code, 201, added.text)
        gift = self.gifts.get_gift_by_id(added.json()['gift_id'])
        self.assertEqual(gift.title, 'Book')
        self.assertEqual([tag.name for tag in gift.tags], ['Книги'])
        self.assertEqual(len(self.client.get('/wishes/',headers=self.owner).json()),1)
        self.assertEqual(self.client.put(f'/wishes/{wish_id}',headers=self.owner,json={'title':'New title','price':120}).json()['title'],'New title')
        self.assertEqual(self.client.patch(f'/wishes/{wish_id}/received',headers=self.owner,json={'received':True}).status_code,200)
        self.assertEqual(self.client.post(f'/wishes/{wish_id}/events',headers=self.owner,json={'event_id':self.event.id}).status_code,404)

    def test_delete_with_keep_preserves_gift_tags_and_received(self):
        tag = TagRepository().create_tag(Tag(event_id=self.event.id,name='Техника'))
        gift = self.gifts.create_gift(Gift(event_id=self.event.id,title='Phone',price=500), [tag.id])
        with get_connection() as db: db.execute('UPDATE gifts SET received=1 WHERE id=?',(gift.id,))
        self.assertEqual(self.client.delete(f'/events/{self.event.id}?keep_gifts=true',headers=self.other).status_code,403)
        response = self.client.delete(f'/events/{self.event.id}?keep_gifts=true',headers=self.owner)
        self.assertEqual(response.status_code,200,response.text)
        wishes = self.client.get('/wishes/',headers=self.owner).json()
        self.assertEqual(len(wishes),1)
        self.assertEqual((wishes[0]['title'],wishes[0]['tags'],wishes[0]['received']),('Phone',['Техника'],True))
        self.assertIsNone(self.events.get_event_by_id(self.event.id))

    def test_delete_without_keep_does_not_add_wishes(self):
        self.gifts.create_gift(Gift(event_id=self.event.id,title='Book',price=50))
        self.assertEqual(self.client.delete(f'/events/{self.event.id}',headers=self.owner).status_code,200)
        self.assertEqual(self.client.get('/wishes/',headers=self.owner).json(),[])

    def test_share_only_explicitly_selected_items(self):
        one = self.client.post('/wishes/',headers=self.owner,json={'title':'Book','price':100}).json()
        self.client.post('/wishes/',headers=self.owner,json={'title':'Private'}).json()
        self.assertEqual(self.client.post('/wish-shares/',headers=self.other,json={'items':[{'kind':'wish','id':one['id']}]}).status_code,404)
        result = self.client.post('/wish-shares/',headers=self.owner,json={'items':[{'kind':'wish','id':one['id']}]} )
        self.assertEqual(result.status_code,201,result.text)
        token = result.json()['token']
        shared = self.client.get(f'/wish-shares/{token}')
        self.assertEqual(shared.status_code,200)
        self.assertEqual([item['title'] for item in shared.json()['items']],['Book'])
        self.assertNotIn('owner_id', shared.json()['items'][0])
        self.assertEqual(self.client.get('/wish-shares/invalid').status_code,404)

    def test_priority_is_saved_and_copied_to_event(self):
        wish = self.client.post('/wishes/',headers=self.owner,json={'title':'Phone','price':100,'priority':'high'}).json()
        self.assertEqual(wish['priority'],'high')
        created = self.client.post(f'/wishes/{wish["id"]}/events',headers=self.owner,json={'event_id':self.event.id}).json()
        self.assertEqual(self.gifts.get_gift_by_id(created['gift_id']).priority,'high')

    def test_price_optional_but_required_for_event(self):
        wish = self.client.post('/wishes/',headers=self.owner,json={'title':'Surprise'}).json()
        result = self.client.post(f'/wishes/{wish["id"]}/events',headers=self.owner,json={'event_id':self.event.id})
        self.assertEqual(result.status_code,422)
        self.assertEqual(self.client.delete(f'/wishes/{wish["id"]}',headers=self.other).status_code,404)
        self.assertEqual(self.client.delete(f'/wishes/{wish["id"]}',headers=self.owner).status_code,200)

    def test_shared_personal_wish_reservations_are_live_and_private(self):
        wish = self.client.post('/wishes/', headers=self.owner, json={'title':'Book','price':100}).json()
        def share():
            return self.client.post('/wish-shares/',headers=self.owner,json={'items':[{'kind':'wish','id':wish['id']}]}).json()['token']
        first, second = share(), share()
        url = f'/wish-shares/{first}/items/0/reservation'
        self.assertEqual(self.client.post(url,headers=self.owner,json={}).status_code,403)
        self.assertEqual(self.client.post(url,json={'name':'Guest','secret_word':'snow'}).status_code,200)
        self.assertEqual(self.client.get(f'/wish-shares/{second}').json()['items'][0]['status'],'reserved')
        self.assertEqual(self.client.get(f'/wish-shares/{first}',headers=self.owner).json()['items'][0]['status'],'hidden')
        self.assertEqual(self.client.post(f'/wish-shares/{second}/items/0/reservation',headers=self.other,json={}).status_code,409)
        self.assertEqual(self.client.request('DELETE',url,json={'secret_word':'wrong'}).status_code,403)
        self.assertEqual(self.client.request('DELETE',url,json={'secret_word':'snow'}).status_code,200)
        self.assertEqual(self.client.post(url,headers=self.other,json={}).status_code,200)
        self.assertTrue(self.client.get(f'/wish-shares/{second}',headers=self.other).json()['items'][0]['is_mine'])
        self.assertEqual(self.client.request('DELETE',url,headers=self.other,json={}).status_code,200)
        self.assertEqual(self.client.get(f'/wish-shares/{first}').json()['items'][0]['status'],'available')

    def test_event_gift_reservation_from_share_uses_existing_reservation(self):
        gift = self.gifts.create_gift(Gift(event_id=self.event.id,title='Game',price=100))
        token = self.client.post('/wish-shares/',headers=self.owner,json={'items':[{'kind':'gift','id':gift.id}]}).json()['token']
        url = f'/wish-shares/{token}/items/0/reservation'
        self.assertNotIn('fundraising', self.client.get(f'/wish-shares/{token}').json()['items'][0])
        self.assertEqual(self.client.post(url,headers=self.other,json={}).status_code,200)
        self.assertEqual(self.gifts.get_gift_by_id(gift.id).status,'reserved')
        self.assertEqual(self.client.request('DELETE',url,headers=self.other,json={}).status_code,200)
        self.assertEqual(self.gifts.get_gift_by_id(gift.id).status,'available')

    def test_shared_fundraising_gift_exposes_progress_without_reservation(self):
        event = self.events.create_event(Event(owner_id=1, title='Fundraiser', public_token='fundraising-token'))
        gift = self.gifts.create_gift(Gift(event_id=event.id, title='Laptop', price=1000, contribution_goal=1000))
        ContributionRepository().create_contribution(Contribution(
            gift_id=gift.id, amount=250, contributor_name='Guest', is_anonymous=False,
        ))

        response = self.client.post('/wish-shares/', headers=self.owner, json={'items': [{'kind': 'gift', 'id': gift.id}]})
        self.assertEqual(response.status_code, 201, response.text)
        token = response.json()['token']
        item = self.client.get(f'/wish-shares/{token}').json()['items'][0]
        self.assertEqual(item['status'], 'available')
        self.assertEqual(item['fundraising'], {
            'id': gift.id,
            'contribution_goal': 1000,
            'contribution_total': 250,
            'status': 'available',
            'public_token': 'fundraising-token',
        })

        reservation = self.client.post(
            f'/wish-shares/{token}/items/0/reservation',
            json={'name': 'Guest', 'secret_word': 'snow'},
        )
        self.assertEqual(reservation.status_code, 409, reservation.text)
