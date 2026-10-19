from dataclasses import replace


def owner_gift_response(gift, show_reservations=False):
    if show_reservations:
        return gift
    return replace(gift, status="available", reservation_id=None)


def owner_gift_filters(filters):
    # Filtering by a hidden status must not reveal it through result membership.
    if not filters.show_reservations:
        return filters.model_copy(update={"status": None})
    return filters
