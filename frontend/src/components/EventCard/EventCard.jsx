import "./EventCard.css"

function EventCard({ id, title, description, place, date, onDeleteEvent }) {
    return(
        <div className="event-card">
            <div className="event-card-header">

                <div className="event-card-info">
                    <h2>{title}</h2>
                    <p>{description}</p>
                </div>

                <div className="event-card-actions">
                    <button className="edit-button">Изменить</button>
                    <button className="delete-button" onClick={() => onDeleteEvent(id)}>Удалить</button>
                </div>

            </div>
            
            <div className="event-card-footer">
                <span>{place}</span>
                <span>{date}</span>
            </div>
        </div>
    )
}

export default EventCard
