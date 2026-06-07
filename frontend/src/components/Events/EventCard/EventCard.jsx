import "./EventCard.css"

function EventCard({ event, onDeleteEvent, onOpenEvent }) {
    return(
        <div
            className="event-card"
            onClick={() => onOpenEvent(event.id)}
        >
            <div className="event-card-header">

                <div className="event-card-info">
                    <h2>{event.title}</h2>
                    <p>{event.description}</p>
                </div>

                <div className="event-card-actions">
                    <button 
                        className="edit-button"
                        onClick={(clickEvent) => {
                            clickEvent.preventDefault()
                            clickEvent.stopPropagation()
                        }}
                    >
                        Изменить
                    </button>

                    <button 
                        className="delete-button"
                        onClick={(clickEvent) => {
                            clickEvent.preventDefault()
                            clickEvent.stopPropagation()
                            onDeleteEvent(event.id)
                        }}
                    >
                        Удалить
                    </button>
                </div>

            </div>
            
            <div className="event-card-footer">
                <span>{event.place}</span>
                <span>{event.event_date}</span>
            </div>
        </div>
    )
}

export default EventCard
