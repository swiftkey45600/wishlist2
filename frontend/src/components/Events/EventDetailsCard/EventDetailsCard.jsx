import "./EventDetailsCard.css"
import { useState } from "react"
import { resolveImageUrl } from "../../../application/imageApplication"
import { getLocationCoordinates, withoutLocationCoordinates } from "../LocationPicker/location"

function EventDetailsCard({ event, onShare, onEdit, onDelete }) {
    const [failedCoverUrl, setFailedCoverUrl] = useState("")
    const coverUrl = resolveImageUrl(
        event.cover_image_id,
        event.cover_image_url || event.cover_url
    )
    const coordinates = getLocationCoordinates(event.place)
    const placeLabel = coordinates ? withoutLocationCoordinates(event.place) : event.place
    const eventDate = event.event_date ? new Date(event.event_date) : null
    const formattedDate = eventDate
        ? eventDate.toLocaleDateString("ru-RU", {
              day: "2-digit",
              month: "2-digit",
              year: "numeric"
          })
        : ""

    const formattedTime = eventDate && !Number.isNaN(eventDate.getTime()) && event.event_date.includes("T")
        ? eventDate.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" }) : ""

    const endDate = event.end_date ? new Date(event.end_date) : null
    const formattedEndDate = endDate && !Number.isNaN(endDate.getTime())
        ? endDate.toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit", year: "numeric" }) : ""

    return (
        <div className="event-details-card">
            <div className="event-cover">
                {coverUrl && coverUrl !== failedCoverUrl
                    ? <img className="event-cover-image" src={coverUrl} onError={() => setFailedCoverUrl(coverUrl)} alt={`Обложка события «${event.title}»`} />
                    : <div className="event-icon">🎂</div>}
            </div>
            <div className="event-info">
                <div>
                    <h1>{event.title}</h1>
                    <div className="event-meta">
                        {formattedDate && <span>{formattedDate}{formattedTime ? `, ${formattedTime}` : ""}{formattedEndDate && formattedEndDate !== formattedDate ? ` — ${formattedEndDate}` : ""}</span>}
                        {event.place && (coordinates ? <a href={`https://www.openstreetmap.org/?mlat=${coordinates[0]}&mlon=${coordinates[1]}#map=16/${coordinates[0]}/${coordinates[1]}`} target="_blank" rel="noopener noreferrer">{placeLabel} ↗</a> : <span>{event.place}</span>)}
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
