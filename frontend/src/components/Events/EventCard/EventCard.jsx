import "./EventCard.css"

function formatEventDate(value) {
    if (!value) return "Дата не указана"
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return value
    return date.toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" })
}

function EventCard({ event, gifts, onOpenEvent, onEditEvent }) {
    return (
        <div className="event-card" onClick={() => onOpenEvent(event.id)}>
            <div className="event-card-header">
                <div className="event-card-info">
                    <h2 className="event-card-title">{event.title || "Без названия"}</h2>
                    {event.description && <p className="event-card-description">{event.description}</p>}
                    <p className="event-card-date">{formatEventDate(event.event_date)}{event.place ? ` · ${event.place}` : ""}</p>
                </div>
                {onEditEvent && <button className="event-secondary" onClick={(clickEvent) => { clickEvent.stopPropagation(); onEditEvent(event) }}>Изменить</button>}
            </div>
            <div className="event-card-gifts">
                {gifts.length === 0 && <p className="empty-gifts">Пока нет подарков для этого события.</p>}
                {gifts.map((gift) => (
                    <div className="event-gift-row" key={gift.id}>
                        <div className="event-gift-picture">{gift.picture_url ? <img src={gift.picture_url} alt="" /> : "🎁"}</div>
                        <div className="event-gift-info"><strong>{gift.title}</strong><span>{gift.description || "Описание подарка не указано"}</span></div>
                        <div className="event-gift-right"><strong>{gift.price} ₽</strong><span className={`gift-badge ${gift.status}`}>{gift.status}</span></div>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default EventCard
