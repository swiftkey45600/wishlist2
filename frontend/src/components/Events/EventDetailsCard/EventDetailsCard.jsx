import "./EventDetailsCard.css"

function EventDetailsCard({ event }) {
    const eventDate = event.event_date ? new Date(event.event_date) : null
    const formattedDate = eventDate
        ? eventDate.toLocaleDateString("ru-RU", {
              day: "2-digit",
              month: "2-digit",
              year: "numeric"
          })
        : ""

    const formattedTime = eventDate
        ? eventDate.toLocaleTimeString("ru-RU", {
              hour: "2-digit",
              minute: "2-digit"
          })
        : ""

    return (
        <div className="event-details-card">
            <img
                className="event-image"
                src={event.image || "https://via.placeholder.com/600x320?text=No+Image"}
                alt={event.title || "Событие"}
            />

            <div className="event-info">
                <h1>{event.title}</h1>
                <p>{event.description}</p>

                <div className="event-meta">
                    {formattedDate && <span>📆 {formattedDate}</span>}
                    {formattedTime && <span>🕒 {formattedTime}</span>}
                    {event.place && <span>📍 {event.place}</span>}
                </div>
            </div>
        </div>
    )
}

export default EventDetailsCard
