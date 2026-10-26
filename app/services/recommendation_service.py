from collections import Counter
from statistics import median
from urllib.parse import urlsplit, urlunsplit

from app.repositories.event_repository import EventRepository
from app.repositories.gift_repository import GiftRepository


def product_key(gift):
    title = gift.title.strip().casefold()
    if not gift.marketplace_url:
        return title
    try:
        url = urlsplit(gift.marketplace_url)
    except ValueError:
        return title
    if url.scheme not in {"http", "https"} or not url.netloc:
        return title
    return urlunsplit((url.scheme.lower(), url.netloc.lower(), url.path.rstrip('/'), '', ''))


def product_url(value):
    if not value:
        return None
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    return value if parsed.scheme in {"http", "https"} and parsed.netloc else None


class RecommendationService:
    def get_recommendations(self, event, limit=6):
        repository = GiftRepository()
        current = repository.get_gifts_by_event(event.id)
        existing_keys = {product_key(gift) for gift in current}
        existing_titles = {gift.title.strip().casefold() for gift in current}
        tags = {tag.name.casefold() for gift in current for tag in gift.tags}
        prices = [gift.price for gift in current if gift.price and gift.price > 0]
        target_price = median(prices) if prices else None
        candidates = repository.get_recommendation_candidates(event.owner_id, event.id)
        own_event_ids = {source.id for source in EventRepository().get_events_by_user(event.owner_id)}
        popularity = Counter(product_key(gift) for gift in candidates)

        def rank(gift):
            shared_tags = len(tags & {tag.name.casefold() for tag in gift.tags})
            distance = abs(gift.price - target_price) / max(target_price, 1) if target_price else 0
            return (-shared_tags, distance, -popularity[product_key(gift)], gift.id)

        result = []
        seen = set(existing_keys)
        for gift in sorted(candidates, key=rank):
            key = product_key(gift)
            title = gift.title.strip().casefold()
            if key in seen or title in existing_titles:
                continue
            seen.add(key)
            existing_titles.add(title)
            result.append({
                "id": len(result) + 1,
                "title": gift.title,
                "price": gift.price,
                "description": gift.description if gift.event_id in own_event_ids else None,
                "picture_url": f"/images/{gift.image_id}" if gift.image_id else product_url(gift.picture_url),
                "marketplace_url": product_url(gift.marketplace_url),
            })
            if len(result) >= limit:
                break
        return result
