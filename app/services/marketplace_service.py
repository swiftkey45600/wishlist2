import base64
import binascii
import hashlib
import ipaddress
import json
import math
import re
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from html.parser import HTMLParser
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, unquote, urljoin, urlparse
from urllib.request import HTTPCookieProcessor, HTTPRedirectHandler, Request, build_opener
from uuid import uuid4

from app.config import UPLOAD_DIR
from app.models.image import Image
from app.repositories.image_repository import ImageRepository
from app.utils.images import ImageValidationError, MAX_IMAGE_SIZE, validate_image_bytes


MAX_PAGE_SIZE = 3 * 1024 * 1024
CACHE_TTL_SECONDS = 10 * 60
REQUEST_TIMEOUT_SECONDS = 8
WB_TIMEOUT_SECONDS = 3
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}
PREVIEW_USER_AGENTS = ("WhatsApp/2.23.20.0", "TelegramBot (like TwitterBot)")
JSON_META_PATTERN = re.compile(
    r'"(?:property|name)"\s*:\s*"((?:og|twitter|product):[a-z:_]+)"\s*,\s*"content"\s*:\s*"((?:[^"\\]|\\.)*)"',
    flags=re.IGNORECASE,
)
CHALLENGE_TITLE_MARKERS = (
    "доступ ограничен", "доступ к сайту ограничен", "подтвердите, что",
    "подтвердите что", "access denied", "just a moment", "captcha",
    "are you a robot", "security check", "проверка безопасности",
    "antibot", "challenge page", "нет соединения", "вы не робот",
)

# Верхняя граница vol для каждой корзины CDN Wildberries.
WB_BASKET_LIMITS = (
    (143, 1), (287, 2), (431, 3), (719, 4), (1007, 5), (1061, 6), (1115, 7),
    (1169, 8), (1313, 9), (1601, 10), (1655, 11), (1919, 12), (2045, 13),
    (2189, 14), (2405, 15), (2621, 16), (2837, 17), (3053, 18), (3269, 19),
    (3485, 20), (3701, 21), (3917, 22), (4133, 23), (4349, 24), (4565, 25),
)
WB_MAX_BASKET = 40


class MarketplaceParseError(Exception):
    def __init__(self, message: str, url: str | None = None):
        super().__init__(message)
        self.url = url


class _UnsafeMarketplaceUrl(MarketplaceParseError):
    pass


class _ValidatedRedirectHandler(HTTPRedirectHandler):
    def __init__(self, validate_url):
        self.validate_url = validate_url

    def redirect_request(self, req, fp, code, msg, headers, new_url):
        # Validate before the next request, including redirects to image URLs.
        safe_url = self.validate_url(new_url)
        return super().redirect_request(req, fp, code, msg, headers, safe_url)


class _ProductMetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.metadata: dict[str, str] = {}
        self.title_parts: list[str] = []
        self.json_ld_parts: list[str] = []
        self._json_ld_buffer: list[str] = []
        self._in_title = False
        self._in_json_ld = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name.lower(): value for name, value in attrs if value is not None}
        if tag.lower() == "meta":
            key = (
                attributes.get("property")
                or attributes.get("name")
                or attributes.get("itemprop")
            )
            content = attributes.get("content")
            if key and content:
                self.metadata.setdefault(key.lower(), content.strip())
        elif tag.lower() == "title":
            self._in_title = True
        elif tag.lower() == "script" and "ld+json" in attributes.get("type", "").lower():
            self._in_json_ld = True
            self._json_ld_buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False
        elif tag.lower() == "script" and self._in_json_ld:
            self.json_ld_parts.append("".join(self._json_ld_buffer))
            self._in_json_ld = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
        if self._in_json_ld:
            self._json_ld_buffer.append(data)


class MarketplaceService:
    def __init__(self, image_repository: ImageRepository):
        self.image_repository = image_repository
        self._cache: dict[str, tuple[float, dict]] = {}

    def parse_product(self, url: str, owner_id: int | None = None) -> dict:
        normalized_url = self._validate_url(url)
        cached = self._cache.get(normalized_url)
        if (
            cached
            and time.monotonic() - cached[0] < CACHE_TTL_SECONDS
            and self.image_repository.get_image_by_id(cached[1]["image_id"]) is not None
        ):
            return deepcopy(cached[1])

        final_url = normalized_url
        warning = None
        try:
            product = self._parse_wildberries(normalized_url)
            if product is None:
                product, final_url = self._parse_page(normalized_url)
            else:
                final_url = product["marketplace_url"]
        except _UnsafeMarketplaceUrl:
            raise
        except MarketplaceParseError as error:
            if error.url:
                final_url = self._validate_url(error.url)
            product = self._product_from_url(final_url) or self._product_from_url(normalized_url)
            if product is None:
                raise
            warning = "Магазин не отдал карточку товара. Название взято из ссылки; проверьте его и укажите цену вручную."
        product["marketplace_url"] = final_url
        if warning is None and product.get("price") is None:
            warning = "Магазин не отдал цену товара. Укажите её вручную."
        product["warning"] = warning

        source_image_url = product.pop("source_image_url", None)
        product["image_id"] = None
        product["picture_url"] = urljoin(final_url, source_image_url) if source_image_url else None
        if source_image_url:
            try:
                image = self._download_image(urljoin(final_url, source_image_url), owner_id)
            except MarketplaceParseError:
                image = None
            if image is not None:
                product["image_id"] = image.id
                product["picture_url"] = f"/images/{image.id}"

        # Allow a retry after a temporary block or failed image download.
        if product["image_id"] is not None:
            self._cache[normalized_url] = (time.monotonic(), deepcopy(product))
        return product

    def _parse_page(self, url: str) -> tuple[dict, str]:
        agents = (BROWSER_HEADERS["User-Agent"],)
        hostname = (urlparse(url).hostname or "").lower().rstrip(".")
        if any(hostname == domain or hostname.endswith(f".{domain}") for domain in (
            "ozon.ru", "wildberries.ru", "market.yandex.ru", "aliexpress.ru", "aliexpress.com",
        )):
            agents += PREVIEW_USER_AGENTS
        request_url = url
        best_result = None
        last_error = MarketplaceParseError("Не удалось загрузить страницу маркетплейса")
        for agent in agents:
            try:
                html, final_url = self._download_page(request_url, user_agent=agent)
                product = self._parse_html(html, final_url)
            except _UnsafeMarketplaceUrl:
                raise
            except MarketplaceParseError as error:
                last_error = error
                if error.url and self._product_from_url(error.url) is not None:
                    request_url = self._validate_url(error.url)
                continue
            if product["source_image_url"]:
                return product, final_url
            if best_result is None:
                best_result = (product, final_url)
        if best_result is not None:
            return best_result
        raise MarketplaceParseError(str(last_error), request_url)

    @staticmethod
    def _yandex_captcha_product_url(url: str) -> str | None:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower().rstrip(".")
        if hostname != "market.yandex.ru" or not parsed.path.startswith("/showcaptcha"):
            return None
        values = parse_qs(parsed.query).get("retpath", [])
        if not values:
            return None
        encoded = values[0].split(",", 1)[0]
        try:
            decoded = base64.b64decode(
                encoded + "=" * (-len(encoded) % 4), altchars=b"-_", validate=True
            ).decode("utf-8")
            target = urlparse(decoded)
        except (binascii.Error, UnicodeError, ValueError):
            return None
        if (
            target.scheme not in {"http", "https"}
            or (target.hostname or "").lower().rstrip(".") != "market.yandex.ru"
            or target.username or target.password
        ):
            return None
        # Sharing/tracking parameters are unnecessary when retrying the card.
        canonical_url = target._replace(query="", fragment="").geturl()
        if MarketplaceService._product_from_url(canonical_url) is None:
            return None
        return canonical_url

    def _parse_wildberries(self, url: str) -> dict | None:
        # Страницы WB закрыты антиботом, но карточка товара и фото лежат на открытом CDN.
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        if not any(hostname == domain or hostname.endswith(f".{domain}") for domain in ("wildberries.ru", "wb.ru")):
            return None
        match = re.search(r"/catalog/(\d+)", parsed.path)
        if not match:
            return None

        article = int(match.group(1))
        basket_url, card = self._find_wildberries_card(article)
        title = card.get("imt_name") or card.get("subj_name")
        if not title:
            raise MarketplaceParseError("Не удалось найти товар Wildberries по этой ссылке")
        photo_count = (card.get("media") or {}).get("photo_count") or 0
        return {
            "title": " ".join(str(title).split()),
            "price": self._wildberries_price(article),
            "description": (card.get("description") or "").strip()[:1000] or None,
            "source_image_url": f"{basket_url}/images/big/1.webp" if photo_count else None,
            "marketplace_url": f"https://www.wildberries.ru/catalog/{article}/detail.aspx",
        }

    def _find_wildberries_card(self, article: int) -> tuple[str, dict]:
        basket_urls = self._wildberries_basket_urls(article)

        def load(basket_url: str) -> tuple[str, dict] | None:
            try:
                return basket_url, self._download_json(f"{basket_url}/info/ru/card.json")
            except MarketplaceParseError:
                return None

        # Обычно угадываем с первого раза, иначе опрашиваем остальные корзины параллельно.
        found = load(basket_urls[0])
        if found is None:
            with ThreadPoolExecutor(max_workers=10) as executor:
                found = next(
                    (result for result in executor.map(load, basket_urls[1:]) if result),
                    None,
                )
        if found is None:
            raise MarketplaceParseError("Не удалось найти товар Wildberries по этой ссылке")
        return found

    @staticmethod
    def _wildberries_basket_urls(article: int) -> list[str]:
        vol = article // 100000
        part = article // 1000
        guess = next(
            (number for limit, number in WB_BASKET_LIMITS if vol <= limit),
            WB_BASKET_LIMITS[-1][1] + 1,
        )
        # Таблица корзин у WB растёт, поэтому после угаданной пробуем соседние.
        numbers = [guess] + [n for n in range(1, WB_MAX_BASKET + 1) if n != guess]
        return [
            f"https://basket-{number:02d}.wbbasket.ru/vol{vol}/part{part}/{article}"
            for number in numbers
        ]

    def _wildberries_price(self, article: int) -> int | None:
        try:
            data = self._download_json(
                "https://card.wb.ru/cards/v2/detail"
                f"?appType=1&curr=rub&dest=-1257786&nm={article}"
            )
        except MarketplaceParseError:
            return None
        products = (data.get("data") or {}).get("products") or []
        for size in (products[0].get("sizes") or []) if products else []:
            price = (size.get("price") or {}).get("product")
            if price:
                return round(price / 100)
        return None

    def _download_json(self, url: str) -> dict:
        url = self._validate_url(url)
        request = Request(url, headers={**BROWSER_HEADERS, "Accept": "application/json"})
        try:
            with self._open_url(request, timeout=WB_TIMEOUT_SECONDS) as response:
                value = json.loads(response.read(MAX_PAGE_SIZE))
        except (HTTPError, URLError, TimeoutError, socket.timeout, ValueError) as error:
            raise MarketplaceParseError("Не удалось загрузить данные товара") from error
        if not isinstance(value, dict):
            raise MarketplaceParseError("Не удалось загрузить данные товара")
        return value

    def _open_url(self, request: Request, timeout: float = REQUEST_TIMEOUT_SECONDS):
        opener = build_opener(
            _ValidatedRedirectHandler(self._validate_url),
            HTTPCookieProcessor(CookieJar()),
        )
        return opener.open(request, timeout=timeout)

    def _download_page(self, url: str, user_agent: str | None = None) -> tuple[str, str]:
        headers = {**BROWSER_HEADERS, "User-Agent": user_agent or BROWSER_HEADERS["User-Agent"]}
        request = Request(url, headers=headers)
        try:
            with self._open_url(request) as response:
                final_url = self._validate_url(response.geturl())
                content_type = response.headers.get_content_type()
                if content_type not in {"text/html", "application/xhtml+xml"}:
                    raise MarketplaceParseError("Ссылка не ведёт на HTML-страницу товара", final_url)
                # Product metadata is near the start; large page tails need not be downloaded.
                body = response.read(MAX_PAGE_SIZE)
                charset = response.headers.get_content_charset() or "utf-8"
        except HTTPError as error:
            if error.code == 401:
                raise MarketplaceParseError(
                    "Сайт требует авторизацию для просмотра товара. "
                    "Попробуйте другую ссылку или заполните данные вручную",
                    error.geturl(),
                ) from error
            if error.code in {307, 403, 429, 498}:
                raise MarketplaceParseError(
                    "Сайт заблокировал автоматическое чтение карточки. "
                    "Заполните данные товара вручную",
                    error.geturl(),
                ) from error
            raise MarketplaceParseError(
                f"Маркетплейс вернул ошибку HTTP {error.code}", error.geturl()
            ) from error
        except (URLError, TimeoutError, socket.timeout) as error:
            raise MarketplaceParseError("Не удалось загрузить страницу маркетплейса") from error

        try:
            return body.decode(charset, errors="replace"), final_url
        except LookupError as error:
            raise MarketplaceParseError("Неизвестная кодировка страницы товара", final_url) from error

    @staticmethod
    def _product_from_url(url: str) -> dict | None:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower().rstrip(".")
        path = unquote(parsed.path)
        patterns = (
            ("ozon.ru", "Ozon", r"/product/(?:(?P<slug>[^/]+)-)?(?P<id>\d+)(?:/|$)"),
            ("wildberries.ru", "Wildberries", r"/catalog/(?P<id>\d+)/detail\.aspx/?$"),
            ("market.yandex.ru", "Яндекс Маркета", r"/(?:product--|card/)(?P<slug>[^/]+)/(?P<id>\d+)(?:/|$)"),
            ("market.yandex.ru", "Яндекс Маркета", r"/product/(?P<id>\d+)(?:/|$)"),
            ("aliexpress.ru", "AliExpress", r"/item/(?P<id>\d+)\.html$"),
            ("aliexpress.com", "AliExpress", r"/item/(?P<id>\d+)\.html$"),
        )
        for domain, name, pattern in patterns:
            if hostname != domain and not hostname.endswith(f".{domain}"):
                continue
            match = re.search(pattern, path, flags=re.IGNORECASE)
            if not match:
                continue
            slug = match.groupdict().get("slug")
            title = " ".join(slug.replace("-", " ").split()) if slug else ""
            return {
                "title": title or f"Товар {name} №{match.group('id')}",
                "price": None,
                "source_image_url": None,
            }
        return None

    def _parse_html(self, html: str, page_url: str) -> dict:
        parsed_url = urlparse(page_url)
        if (
            (parsed_url.hostname or "").lower().rstrip(".") == "market.yandex.ru"
            and parsed_url.path.startswith("/showcaptcha")
        ):
            raise MarketplaceParseError(
                "Маркетплейс показал CAPTCHA вместо товара",
                self._yandex_captcha_product_url(page_url),
            )
        parser = _ProductMetadataParser()
        parser.feed(html)
        page_title = " ".join(parser.title_parts).lower()
        if any(marker in page_title for marker in CHALLENGE_TITLE_MARKERS):
            raise MarketplaceParseError("Маркетплейс показал проверку на робота вместо товара", page_url)
        self._reject_challenge_page(html, page_url)
        product_node = self._find_product_node(parser.json_ld_parts)
        metadata = parser.metadata
        # Some stores include Open Graph tags in JSON for client rendering.
        for match in JSON_META_PATTERN.finditer(html):
            try:
                content = json.loads(f'"{match.group(2)}"')
            except json.JSONDecodeError:
                continue
            if content.strip():
                metadata.setdefault(match.group(1).lower(), content.strip())

        title = self._first_value(
            product_node.get("name") if product_node else None,
            metadata.get("og:title"),
            metadata.get("twitter:title"),
            "".join(parser.title_parts).strip(),
        )
        image_url = self._first_value(
            self._json_ld_image(product_node.get("image")) if product_node else None,
            metadata.get("og:image"),
            metadata.get("og:image:secure_url"),
            metadata.get("og:image:url"),
            metadata.get("twitter:image"),
            metadata.get("twitter:image:src"),
            metadata.get("image"),
        )
        price = self._extract_price(product_node, metadata, html, page_url)
        description = self._first_value(
            product_node.get("description") if product_node else None,
            metadata.get("og:description"),
            metadata.get("description"),
        )

        if not title or any(marker in title.lower() for marker in CHALLENGE_TITLE_MARKERS):
            raise MarketplaceParseError("Не удалось определить название товара", page_url)

        return {
            "title": self._clean_title(title, page_url),
            "price": price,
            "description": description[:1000] if description else None,
            "source_image_url": image_url,
        }

    def _extract_price(
        self,
        product_node: dict | None,
        metadata: dict[str, str],
        html: str,
        page_url: str,
    ) -> int | None:
        offers = product_node.get("offers") if product_node else None
        if isinstance(offers, list):
            offers = offers[0] if offers else None
        json_ld_price = None
        if isinstance(offers, dict):
            json_ld_price = offers.get("price") or offers.get("lowPrice")

        candidates = [
            json_ld_price,
            metadata.get("product:price:amount"),
            metadata.get("og:price:amount"),
            metadata.get("price"),
        ]
        for candidate in candidates:
            parsed = self._normalize_price(candidate)
            if parsed is not None:
                return parsed

        hostname = (urlparse(page_url).hostname or "").lower()
        patterns: list[tuple[str, int]] = []
        if hostname.endswith("ozon.ru"):
            patterns = [(r'"(?:cardPrice|price)"\s*:\s*"?([^",}]+)', 1)]
        elif hostname.endswith("wildberries.ru"):
            patterns = [(r'"salePriceU"\s*:\s*(\d+)', 100)]
        elif hostname.endswith("market.yandex.ru"):
            patterns = [(r'"price"\s*:\s*\{\s*"currency"\s*:\s*"RU[RB]"\s*,\s*"value"\s*:\s*"(\d+)"', 1)]

        for pattern, divisor in patterns:
            match = re.search(pattern, html, flags=re.IGNORECASE)
            if match:
                parsed = self._normalize_price(match.group(1))
                if parsed is not None:
                    return round(parsed / divisor)
        return None

    def _download_image(self, url: str, owner_id: int | None = None) -> Image:
        image_url = self._validate_url(url)
        request = Request(image_url, headers={**BROWSER_HEADERS, "Accept": "image/webp,image/*;q=0.9,*/*;q=0.8"})
        try:
            with self._open_url(request) as response:
                content_type = response.headers.get_content_type().lower()
                if content_type not in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
                    raise MarketplaceParseError("Файл товара не является изображением")
                image_bytes = response.read(MAX_IMAGE_SIZE + 1)
        except (HTTPError, URLError, TimeoutError, socket.timeout) as error:
            raise MarketplaceParseError("Не удалось скачать изображение товара") from error

        try:
            validated_image = validate_image_bytes(image_bytes, content_type)
        except ImageValidationError as error:
            raise MarketplaceParseError(str(error)) from error

        image_hash = hashlib.sha256(image_bytes).hexdigest()
        existing = self.image_repository.get_image_by_hash(image_hash)
        if existing is not None:
            return existing

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        image_path = UPLOAD_DIR / f"{uuid4().hex}{validated_image.extension}"
        image_path.write_bytes(image_bytes)
        try:
            return self.image_repository.create_image(
                Image(image_path=str(image_path), image_type=content_type, hash=image_hash, owner_id=owner_id)
            )
        except ValueError:
            image_path.unlink(missing_ok=True)
            existing = self.image_repository.get_image_by_hash(image_hash)
            if existing is None:
                raise MarketplaceParseError("Не удалось сохранить изображение товара")
            return existing

    @staticmethod
    def _find_product_node(json_ld_parts: list[str]) -> dict | None:
        for raw_json in json_ld_parts:
            try:
                value = json.loads(raw_json)
            except (json.JSONDecodeError, TypeError):
                continue
            queue = value if isinstance(value, list) else [value]
            while queue:
                node = queue.pop(0)
                if not isinstance(node, dict):
                    continue
                node_type = node.get("@type")
                node_types = node_type if isinstance(node_type, list) else [node_type]
                if any(str(item).lower() == "product" for item in node_types):
                    return node
                graph = node.get("@graph")
                if isinstance(graph, list):
                    queue.extend(graph)
        return None

    @staticmethod
    def _json_ld_image(value) -> str | None:
        if isinstance(value, str):
            return value
        if isinstance(value, list) and value:
            return MarketplaceService._json_ld_image(value[0])
        if isinstance(value, dict):
            return value.get("url") or value.get("contentUrl")
        return None

    @staticmethod
    def _first_value(*values) -> str | None:
        return next((str(value).strip() for value in values if value), None)

    @staticmethod
    def _normalize_price(value) -> int | None:
        if value is None:
            return None
        normalized = re.sub(r"[^\d,.-]", "", str(value).replace("\xa0", ""))
        if not normalized:
            return None
        if "," in normalized and "." not in normalized:
            normalized = normalized.replace(",", ".")
        elif "," in normalized and "." in normalized:
            normalized = normalized.replace(",", "")
        try:
            price = float(normalized)
        except ValueError:
            return None
        return round(price) if math.isfinite(price) and price >= 0 else None

    @staticmethod
    def _clean_title(title: str, page_url: str) -> str:
        title = " ".join(title.split())
        hostname = (urlparse(page_url).hostname or "").lower()
        suffixes = {
            "ozon.ru": (" | Ozon", " — купить на OZON"),
            "wildberries.ru": (" | Wildberries",),
            "market.yandex.ru": (" — купить на Яндекс Маркете", " / Яндекс Маркет"),
        }
        for domain, domain_suffixes in suffixes.items():
            if hostname == domain or hostname.endswith(f".{domain}"):
                for suffix in domain_suffixes:
                    if title.lower().endswith(suffix.lower()):
                        title = title[: -len(suffix)].strip()
        # «… — купить в интернет-магазине на Яндекс Маркете» и похожие хвосты.
        return re.sub(r"\s+[—–-]\s+купить\b.*$", "", title, flags=re.IGNORECASE).strip()

    @staticmethod
    def _reject_challenge_page(html: str, url: str) -> None:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        if hostname.endswith("market.yandex.ru") and parsed.path.startswith("/showcaptcha"):
            raise MarketplaceParseError(
                "Яндекс Маркет открыл CAPTCHA вместо товара. Попробуйте ещё раз через минуту "
                "или заполните данные вручную"
            )
        title = re.search(r"<title[^>]*>([^<]*)", html[:20000], flags=re.IGNORECASE)
        title_text = title.group(1).lower() if title else ""
        if any(marker in title_text for marker in CHALLENGE_TITLE_MARKERS):
            raise MarketplaceParseError(
                "Сайт показал проверку на робота вместо товара. "
                "Попробуйте ещё раз или заполните данные вручную"
            )
        if hostname.endswith("ozon.ru") and parsed.path.strip("/") == "":
            raise MarketplaceParseError(
                "Ozon открыл главную страницу вместо товара. Проверьте ссылку"
            )

    @staticmethod
    def _validate_url(url: str) -> str:
        try:
            parsed = urlparse(str(url).strip())
            parsed.port
        except ValueError as error:
            raise _UnsafeMarketplaceUrl("Укажите корректную http(s)-ссылку") from error
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise _UnsafeMarketplaceUrl("Укажите корректную http(s)-ссылку")
        if parsed.username or parsed.password:
            raise _UnsafeMarketplaceUrl("Ссылки с логином и паролем не поддерживаются")

        hostname = parsed.hostname.lower().rstrip(".")
        if hostname == "localhost" or hostname.endswith(".localhost"):
            raise _UnsafeMarketplaceUrl("Локальные адреса не поддерживаются")
        try:
            addresses = {item[4][0] for item in socket.getaddrinfo(hostname, parsed.port)}
        except ValueError as error:
            raise _UnsafeMarketplaceUrl("Укажите корректную http(s)-ссылку") from error
        except socket.gaierror as error:
            raise MarketplaceParseError("Не удалось определить адрес сайта") from error
        for address in addresses:
            ip = ipaddress.ip_address(address)
            if not ip.is_global:
                raise _UnsafeMarketplaceUrl("Локальные адреса не поддерживаются")
        return parsed.geturl()
