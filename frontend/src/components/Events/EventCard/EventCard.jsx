import "./EventCard.css"

function EventCard({ event, onDeleteEvent }) {
    return(
        <div className="event-card">
            <div className="event-card-header">

                <div className="event-card-info">
                    <h2>{event.title}</h2>
                    <p>{event.EventCarddescription}</p>
                </div>

                <div className="event-card-actions">
                    <button 
                        className="edit-button"
                        onClick={(event) => {
                            event.preventDefault()
                            event.stopPropagation()
                        }}
                    >
                        Изменить
                    </button>

                    <button 
                        className="delete-button"
                        onClick={(event) => {
                            event.preventDefault()
                            event.stopPropagation()
                            onDeleteEvent(id)
                        }}
                    >
                        Удалить
                    </button>
                </div>

            </div>
            
            <div className="event-card-footer">
                <span>{event.place}</span>
                <span>{event.date}</span>
            </div>
        </div>
    )
}

export default EventCard
