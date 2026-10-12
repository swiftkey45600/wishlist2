import hashlib
import ipaddress
import json
import re
import socket
import time
from copy import deepcopy
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

from app.models.image import Image
from app.repositories.image_repository import ImageRepository


MAX_PAGE_SIZE = 2 * 1024 * 1024
MAX_IMAGE_SIZE = 5 * 1024 * 1024
CACHE_TTL_SECONDS = 10 * 60
REQUEST_TIMEOUT_SECONDS = 5
UPLOAD_DIR = Path("uploads/images")


class MarketplaceParseError(Exception):
    pass


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

    def parse_product(self, url: str) -> dict:
        normalized_url = self._validate_url(url)
        cached = self._cache.get(normalized_url)
        if cached and time.monotonic() - cached[0] < CACHE_TTL_SECONDS:
            return deepcopy(cached[1])

        html, final_url = self._download_page(normalized_url)
        product = self._parse_html(html, final_url)
        product["marketplace_url"] = final_url

        source_image_url = product.pop("source_image_url", None)
        product["image_id"] = None
        product["picture_url"] = source_image_url
        if source_image_url:
            try:
                image = self._download_image(urljoin(final_url, source_image_url))
            except MarketplaceParseError:
                image = None
            if image is not None:
                product["image_id"] = image.id
                product["picture_url"] = f"/images/{image.id}"

        self._cache[normalized_url] = (time.monotonic(), deepcopy(product))
        return product

    def _download_page(self, url: str) -> tuple[str, str]:
        request = Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "Chrome/124.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        try:
            with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                content_type = response.headers.get_content_type()
                if content_type not in {"text/html", "application/xhtml+xml"}:
                    raise MarketplaceParseError("Ссылка не ведёт на HTML-страницу товара")
                body = response.read(MAX_PAGE_SIZE + 1)
                if len(body) > MAX_PAGE_SIZE:
                    raise MarketplaceParseError("Страница товара слишком большая")
                final_url = self._validate_url(response.geturl())
                charset = response.headers.get_content_charset() or "utf-8"
        except HTTPError as error:
            raise MarketplaceParseError(
                f"Маркетплейс вернул ошибку HTTP {error.code}"
            ) from error
        except (URLError, TimeoutError, socket.timeout) as error:
            raise MarketplaceParseError("Не удалось загрузить страницу маркетплейса") from error

        return body.decode(charset, errors="replace"), final_url

    def _parse_html(self, html: str, page_url: str) -> dict:
        parser = _ProductMetadataParser()
        parser.feed(html)
        product_node = self._find_product_node(parser.json_ld_parts)
        metadata = parser.metadata

        title = self._first_value(
            product_node.get("name") if product_node else None,
            metadata.get("og:title"),
            metadata.get("twitter:title"),
            "".join(parser.title_parts).strip(),
        )
        image_url = self._first_value(
            self._json_ld_image(product_node.get("image")) if product_node else None,
            metadata.get("og:image"),
            metadata.get("twitter:image"),
            metadata.get("image"),
        )
        price = self._extract_price(product_node, metadata, html, page_url)

        if not title:
            raise MarketplaceParseError("Не удалось определить название товара")

        return {
            "title": self._clean_title(title, page_url),
            "price": price,
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
            patterns = [(r'"(?:price|value)"\s*:\s*"?(\d[\d\s.,]*)', 1)]

        for pattern, divisor in patterns:
            match = re.search(pattern, html, flags=re.IGNORECASE)
            if match:
                parsed = self._normalize_price(match.group(1))
                if parsed is not None:
                    return round(parsed / divisor)
        return None

    def _download_image(self, url: str) -> Image:
        image_url = self._validate_url(url)
        request = Request(image_url, headers={"User-Agent": "Wishlist2/1.0"})
        try:
            with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                content_type = response.headers.get_content_type().lower()
                if content_type not in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
                    raise MarketplaceParseError("Файл товара не является изображением")
                image_bytes = response.read(MAX_IMAGE_SIZE + 1)
                if not image_bytes or len(image_bytes) > MAX_IMAGE_SIZE:
                    raise MarketplaceParseError("Изображение товара пустое или слишком большое")
        except (HTTPError, URLError, TimeoutError, socket.timeout) as error:
            raise MarketplaceParseError("Не удалось скачать изображение товара") from error

        image_hash = hashlib.sha256(image_bytes).hexdigest()
        existing = self.image_repository.get_image_by_hash(image_hash)
        if existing is not None:
            return existing

        extensions = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/gif": ".gif",
        }
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        image_path = UPLOAD_DIR / f"{uuid4().hex}{extensions[content_type]}"
        image_path.write_bytes(image_bytes)
        try:
            return self.image_repository.create_image(
                Image(image_path=str(image_path), image_type=content_type, hash=image_hash)
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
        return round(price) if price >= 0 else None

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
        return title

    @staticmethod
    def _validate_url(url: str) -> str:
        parsed = urlparse(str(url).strip())
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise MarketplaceParseError("Укажите корректную http(s)-ссылку")
        if parsed.username or parsed.password:
            raise MarketplaceParseError("Ссылки с логином и паролем не поддерживаются")

        hostname = parsed.hostname.lower().rstrip(".")
        if hostname == "localhost" or hostname.endswith(".localhost"):
            raise MarketplaceParseError("Локальные адреса не поддерживаются")
        try:
            addresses = {item[4][0] for item in socket.getaddrinfo(hostname, parsed.port)}
        except socket.gaierror as error:
            raise MarketplaceParseError("Не удалось определить адрес сайта") from error
        for address in addresses:
            ip = ipaddress.ip_address(address)
            if not ip.is_global:
                raise MarketplaceParseError("Локальные адреса не поддерживаются")
        return parsed.geturl()
