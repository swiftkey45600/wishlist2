import "./EventCard.css"
import GiftImage from "../../Gifts/GiftImage/GiftImage"
import { getGiftPriorityLabel } from "../../Gifts/giftPriority"

function formatEventDate(value) {
    if (!value) return "Дата не указана"
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return value
    return date.toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" })
}

function EventCard({ event, gifts, onOpenEvent }) {
    const eventTitle = event.title || event.name || event.event_name || "Без названия"

    return (
        <div className="event-card" onClick={() => onOpenEvent(event.id)}>
            <div className="event-card-header">
                <div className="event-card-info">
                    <h2 className="event-card-title">{eventTitle}</h2>
                    {event.description && <p className="event-card-description">{event.description}</p>}
                    <p className="event-card-date">{formatEventDate(event.event_date)}{event.end_date && event.end_date.slice(0, 10) !== event.event_date?.slice(0, 10) ? ` — ${formatEventDate(event.end_date)}` : ""}{event.place ? ` · ${event.place}` : ""}</p>
                </div>
            </div>
            <div className="event-card-gifts">
                {gifts.length === 0 && <p className="empty-gifts">Пока нет подарков для этого события.</p>}
                {gifts.map((gift) => (
                    <div className="event-gift-row" key={gift.id}>
                        <div className="event-gift-picture">
                            <GiftImage gift={gift} fallbackClassName="event-gift-picture-fallback" />
                        </div>
                        <div className="event-gift-info">
                            <div className="event-gift-title">
                                <strong>{gift.title}</strong>
                                {gift.priority === "high" && (
                                    <span className="event-gift-priority-badge">{getGiftPriorityLabel(gift.priority)}</span>
                                )}
                            </div>
                            <span>{gift.description || "Описание подарка не указано"}</span>
                        </div>
                        <div className="event-gift-right"><strong>{gift.price} ₽</strong></div>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default EventCard
