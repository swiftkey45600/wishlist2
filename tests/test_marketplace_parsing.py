import base64
import os
import unittest
from unittest.mock import Mock, patch
from urllib.parse import quote

os.environ.setdefault("JWT_SECRET_KEY", "marketplace-test-key")

from app.services.marketplace_service import MarketplaceService, MarketplaceParseError


class MarketplaceParsingTests(unittest.TestCase):
    def setUp(self):
        self.service = MarketplaceService(Mock())

    def test_ozon_json_ld_product_and_price(self):
        product = self.service._parse_html('''
            <script type="application/ld+json">{"@graph":[{"@type":"Product",
            "name":"Чайник", "image":[{"url":"https://cdn.example/photo.jpg"}],
            "offers":{"price":"1 299,50"}}]}</script>
        ''', 'https://www.ozon.ru/product/chaynik-123/')
        self.assertEqual(product['title'], 'Чайник')
        self.assertEqual(product['price'], 1300)
        self.assertEqual(product['source_image_url'], 'https://cdn.example/photo.jpg')

    def test_yandex_client_metadata_and_captcha_return_path(self):
        product = self.service._parse_html('''
            {"property":"og:title","content":"Книга — купить на Яндекс Маркете"}
            {"property":"og:image","content":"https://cdn.example/book.jpg"}
            <meta itemprop="price" content="750">
        ''', 'https://market.yandex.ru/product--kniga/123')
        self.assertEqual(product['title'], 'Книга')
        self.assertEqual(product['price'], 750)
        original = 'https://market.yandex.ru/product--kniga/123?tracking=1'
        encoded = base64.urlsafe_b64encode(original.encode()).decode().rstrip('=')
        captcha = 'https://market.yandex.ru/showcaptcha?retpath=' + quote(encoded)
        self.assertEqual(self.service._yandex_captcha_product_url(captcha), original.split('?')[0])

    def test_wildberries_uses_card_cdn(self):
        with patch.object(self.service, '_find_wildberries_card', return_value=(
            'https://basket-01.wbbasket.ru/card',
            {'imt_name': '  Книга  ', 'media': {'photo_count': 1}, 'description': 'Описание'},
        )), patch.object(self.service, '_wildberries_price', return_value=500):
            product = self.service._parse_wildberries('https://www.wildberries.ru/catalog/123/detail.aspx')
        self.assertEqual(product['title'], 'Книга')
        self.assertEqual(product['price'], 500)
        self.assertTrue(product['source_image_url'].endswith('/images/big/1.webp'))
        self.assertIsNone(self.service._parse_wildberries('https://fakewildberries.ru/catalog/123/detail.aspx'))

    def test_antibot_fallback_is_explicit_and_does_not_cache_missing_data(self):
        url = 'https://www.ozon.ru/product/chaynik-123/'
        with patch.object(self.service, '_validate_url', side_effect=lambda value: value), patch.object(
            self.service, '_parse_page', side_effect=MarketplaceParseError('Blocked', url)
        ):
            product = self.service.parse_product(url)
        self.assertEqual(product['title'], 'chaynik')
        self.assertIsNone(product['price'])
        self.assertIsNone(product['image_id'])
        self.assertTrue(product['warning'])
        self.assertNotIn(url, self.service._cache)

    def test_captcha_is_never_product_title(self):
        with self.assertRaises(MarketplaceParseError):
            self.service._parse_html('<title>Подтвердите, что вы не робот</title>', 'https://www.ozon.ru/product/123/')

    def test_malformed_and_private_urls_are_rejected(self):
        for url in ('http://[broken', 'https://example.com:bad/', 'http://localhost/a'):
            with self.subTest(url=url), self.assertRaises(MarketplaceParseError):
                self.service._validate_url(url)
        with patch('app.services.marketplace_service.socket.getaddrinfo', return_value=[(None, None, None, None, ('127.0.0.1', 80))]):
            with self.assertRaises(MarketplaceParseError):
                self.service._validate_url('https://example.com/')

    def test_huge_price_does_not_crash_parser(self):
        self.assertIsNone(self.service._normalize_price('9' * 1000))
