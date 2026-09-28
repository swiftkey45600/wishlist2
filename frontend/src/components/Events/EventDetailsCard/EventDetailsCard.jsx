import "./EventDetailsCard.css"

function EventDetailsCard({ event, onShare, onEdit, onDelete }) {
    const eventDate = event.event_date ? new Date(event.event_date) : null
    const formattedDate = eventDate
        ? eventDate.toLocaleDateString("ru-RU", {
              day: "2-digit",
              month: "2-digit",
              year: "numeric"
          })
        : ""

    return (
        <div className="event-details-card">
            <div className="event-cover">
                <div className="event-icon">🎂</div>
            </div>
            <div className="event-info">
                <div>
                    <h1>{event.title}</h1>
                    <div className="event-meta">
                        {formattedDate && <span>{formattedDate}</span>}
                        {event.place && <span>{event.place}</span>}
                    </div>
                    {event.description && <p>{event.description}</p>}
                </div>
                {(onShare || onEdit || onDelete) && (
                    <div className="event-details-actions">
                        {onShare && <button className="event-secondary" onClick={onShare}>Поделиться</button>}
                        {onEdit && <button className="event-secondary" onClick={onEdit}>Редактировать</button>}
                        {onDelete && <button className="event-danger" onClick={onDelete}>Удалить событие</button>}
                    </div>
                )}
            </div>
        </div>
    )
}

export default EventDetailsCard
