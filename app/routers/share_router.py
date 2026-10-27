from html import escape
from pathlib import Path
import re
from urllib.parse import quote, urljoin, urlsplit

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.repositories.event_repository import EventRepository
from app.repositories.gift_repository import GiftRepository
from app.repositories.image_repository import ImageRepository


router = APIRouter(tags=["share"])
event_repository = EventRepository()
gift_repository = GiftRepository()
image_repository = ImageRepository()


def _public_image_url(value: str | None, origin: str, api_prefix: str) -> str | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    if value.startswith("/images/"):
        value = api_prefix + value
    try:
        url = urljoin(origin + "/", value)
        parts = urlsplit(url)
    except ValueError:
        return None
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return None
    return url


def _gift_count_text(count: int) -> str:
    if 11 <= count % 100 <= 14:
        noun = "подарков"
    elif count % 10 == 1:
        noun = "подарок"
    elif count % 10 in {2, 3, 4}:
        noun = "подарка"
    else:
        noun = "подарков"
    return f"В списке {count} {noun}. Выберите, чем порадовать!"


@router.get("/share/{public_token}", response_class=HTMLResponse)
def get_share_preview(public_token: str, request: Request):
    event = event_repository.get_event_by_public_token(public_token)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    gifts = gift_repository.get_gifts_by_event(event.id)
    origin = f"{request.url.scheme}://{request.url.netloc}"
    # nginx strips /api before proxying to Uvicorn. Direct local requests
    # have no prefix; an ASGI root_path also works without this header.
    api_prefix = request.headers.get(
        "x-forwarded-prefix", request.scope.get("root_path", "")
    ).rstrip("/")
    if not re.fullmatch(r"(?:/[A-Za-z0-9_-]+)*", api_prefix):
        api_prefix = ""

    image_url = None
    image_candidates = [(event.cover_image_id, None)]
    image_candidates.extend((gift.image_id, gift.picture_url) for gift in gifts)
    for image_id, picture_url in image_candidates:
        if image_id is not None:
            image = image_repository.get_image_by_id(image_id)
            if image is not None and Path(image.image_path).is_file():
                image_url = f"{origin}{api_prefix}/images/{image.id}"
        if image_url is None:
            image_url = _public_image_url(picture_url, origin, api_prefix)
        if image_url is not None:
            break

    title = escape(event.title, quote=True)
    description = escape(_gift_count_text(len(gifts)), quote=True)
    public_url = escape(f"{origin}/share/{quote(public_token, safe='')}", quote=True)
    image_meta = ""
    if image_url is not None:
        image_meta = f'<meta property="og:image" content="{escape(image_url, quote=True)}">'

    return HTMLResponse(
        f"""<!DOCTYPE html>
<html lang="ru" prefix="og: https://ogp.me/ns#">
<head>
  <meta charset="utf-8">
  <title>{title} — Wishlist</title>
  <meta name="description" content="{description}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Wishlist">
  <meta property="og:locale" content="ru_RU">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{public_url}">
  {image_meta}
  <link rel="canonical" href="{public_url}">
</head>
<body>
  <h1>{title}</h1>
  <p>{description}</p>
  <a href="{public_url}">Открыть вишлист</a>
</body>
</html>""",
        headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow"},
    )
