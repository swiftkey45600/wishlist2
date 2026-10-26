import io
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("JWT_SECRET_KEY", "debug-flow-tests")

from fastapi.testclient import TestClient
from PIL import Image
from app.database import init_db, get_connection
from app.main import app
from app.services.marketplace_service import MarketplaceService


class DebugApiFlows(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.enterContext(patch('app.database.DATABASE_PATH', self.directory / 'test.db'))
        self.enterContext(patch('app.routers.image_router.UPLOAD_DIR', self.directory / 'images'))
        (self.directory / 'images').mkdir()
        init_db()
        self.client = TestClient(app, raise_server_exceptions=False)
        self.addCleanup(self.client.close)
        response = self.client.post('/auth/register', json={
            'name': 'Tester', 'login': 'debug-user', 'password': 'ValidPass123',
        })
        self.assertEqual(response.status_code, 200, response.text)
        self.client.headers['Authorization'] = 'Bearer ' + response.json()['access_token']
        response = self.client.post('/events/', json={'title': 'Birthday'})
        self.assertEqual(response.status_code, 200, response.text)
        self.event = response.json()['event']

    def test_event_date_can_be_cleared_without_changing_omitted_fields(self):
        path = f'/events/{self.event["id"]}'
        self.assertEqual(self.client.patch(path, json={'event_date': '2027-01-01T12:00', 'place': 'Home'}).status_code, 200)
        response = self.client.patch(path, json={'event_date': None})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(response.json()['event']['event_date'])
        self.assertEqual(response.json()['event']['place'], 'Home')

    def test_owner_cannot_reserve_own_gift_through_legacy_endpoint(self):
        gift = self.client.post('/gifts/', json={'event_id': self.event['id'], 'title': 'Gift', 'price': 100}).json()
        response = self.client.post('/reservations/', json={'gift_id': gift['id'], 'is_anonymous': False})
        self.assertEqual(response.status_code, 403, response.text)
        self.assertEqual(self.client.get(f'/gifts/{gift["id"]}?show_reservations=true').json()['status'], 'available')

    def test_concurrent_registered_reservations_have_one_winner_without_500(self):
        gift = self.client.post('/gifts/', json={'event_id': self.event['id'], 'title': 'Gift', 'price': 100}).json()
        guest = self.client.post('/auth/register', json={'name': 'Guest', 'login': 'guest-user', 'password': 'GuestPass123'}).json()
        barrier = Barrier(2)
        def no_reservation(_gift_id):
            barrier.wait(timeout=10)
            return None
        def reserve(_):
            return self.client.post('/reservations/', json={'gift_id': gift['id'], 'is_anonymous': False},
                headers={'Authorization': 'Bearer ' + guest['access_token']}).status_code
        with patch('app.routers.reservation_router.reservation_service.reservation_repository.get_reservation_by_gift', side_effect=no_reservation):
            with ThreadPoolExecutor(max_workers=2) as executor:
                statuses = list(executor.map(reserve, range(2)))
        self.assertEqual(sorted(statuses), [200, 409])
        with get_connection() as connection:
            self.assertEqual(connection.execute('SELECT count(*) FROM reservations WHERE gift_id=?', (gift['id'],)).fetchone()[0], 1)
            self.assertEqual(connection.execute('SELECT status FROM gifts WHERE id=?', (gift['id'],)).fetchone()[0], 'reserved')

    def test_tagged_gift_create_edit_reload_delete(self):
        response = self.client.post(f'/events/{self.event["id"]}/tags', json={'name': 'Книги'})
        self.assertEqual(response.status_code, 200, response.text)
        tag = response.json()
        self.assertEqual(self.client.get(f'/events/{self.event["id"]}/tags').json(), [tag])
        response = self.client.post('/gifts/', json={
            'event_id': self.event['id'], 'title': 'Книга', 'price': 500, 'tag_ids': [tag['id']],
        })
        self.assertEqual(response.status_code, 200, response.text)
        gift_id = response.json()['id']
        response = self.client.patch(f'/gifts/{gift_id}', json={'title': 'Другая книга', 'tag_ids': [tag['id']]})
        self.assertEqual(response.status_code, 200, response.text)
        response = self.client.get(f'/events/{self.event["id"]}/gifts')
        self.assertEqual(response.json()[0]['tags'], [tag])
        response = self.client.patch(f'/gifts/{gift_id}', json={'tag_ids': []})
        self.assertEqual(response.json()['tags'], [])
        self.assertEqual(self.client.delete(f'/gifts/{gift_id}').status_code, 200)

    def test_import_unicode_url_then_save_with_real_tag(self):
        tag = self.client.post(f'/events/{self.event["id"]}/tags', json={'name': 'Посуда'}).json()
        url = 'https://www.ozon.ru/product/чайник с ручкой-123/'
        normalized = 'https://www.ozon.ru/product/%D1%87%D0%B0%D0%B9%D0%BD%D0%B8%D0%BA%20%D1%81%20%D1%80%D1%83%D1%87%D0%BA%D0%BE%D0%B9-123/'
        def parse_page(received):
            self.assertEqual(received, normalized)
            return {'title': 'Чайник', 'price': 1000, 'source_image_url': 'https://cdn.example/photo.jpg'}, received
        with patch('app.services.marketplace_service.socket.getaddrinfo', return_value=[(0, 0, 0, '', ('93.184.216.34', 443))]), patch.object(
            MarketplaceService, '_parse_page', side_effect=parse_page
        ), patch.object(MarketplaceService, '_download_image', side_effect=OSError('storage unavailable')):
            response = self.client.post('/marketplace/parse', json={'url': url})
        self.assertEqual(response.status_code, 200, response.text)
        product = response.json()
        response = self.client.post('/gifts/', json={
            'event_id': self.event['id'], 'title': product['title'], 'price': product['price'],
            'marketplace_url': product['marketplace_url'], 'picture_url': product['picture_url'], 'tag_ids': [tag['id']],
        })
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['tags'], [tag])

    def test_invalid_gift_values_are_validation_errors_without_partial_writes(self):
        response = self.client.post('/gifts/', json={'event_id': self.event['id'], 'title': 'Gift', 'price': 100})
        gift_id = response.json()['id']
        for data in ({'status': None}, {'status': 'other'}, {'price': 10**30}):
            response = self.client.patch(f'/gifts/{gift_id}', json=data)
            self.assertEqual(response.status_code, 422, response.text)
        response = self.client.post('/gifts/', json={'event_id': self.event['id'], 'title': 'Gift', 'price': 10**30})
        self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(len(self.client.get(f'/events/{self.event["id"]}/gifts').json()), 1)

    def test_rename_login_keeps_session_working(self):
        self.assertEqual(self.client.patch('/users/me', json={'login': 'renamed-user'}).status_code, 200)
        self.assertEqual(self.client.get('/users/me').json()['user']['login'], 'renamed-user')
        self.assertEqual(self.client.get('/events/').status_code, 200)

    def test_upload_fetch_and_missing_file(self):
        data = io.BytesIO()
        Image.new('RGB', (2, 2)).save(data, format='PNG')
        response = self.client.post('/images', files={'file': ('gift.png', data.getvalue(), 'image/png')})
        self.assertEqual(response.status_code, 200, response.text)
        image_id = response.json()['id']
        self.assertEqual(self.client.get(f'/images/{image_id}').status_code, 200)
        for path in (self.directory / 'images').iterdir():
            path.unlink()
        self.assertEqual(self.client.get(f'/images/{image_id}').status_code, 404)

    def test_legacy_gift_without_price_does_not_break_owner_list(self):
        with get_connection() as connection:
            connection.execute('INSERT INTO gifts(event_id, title) VALUES (?, ?)', (self.event['id'], 'Old gift'))
        response = self.client.get(f'/events/{self.event["id"]}/gifts')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(response.json()[0]['price'])
