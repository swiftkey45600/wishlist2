import "./EventsList.css"

import EventCard from "../EventCard/EventCard"

function EventsList({ events, onDeleteEvent, onOpenEvent }) {
    return (
        <div className="events-list">
			<h2>Список событий</h2>
			{
				events.map((event) => 
					<EventCard
                        key={event.id}
						event={event}
						onDeleteEvent={onDeleteEvent}
                        onOpenEvent={onOpenEvent}
					/>
				)
			}
        </div>
    )
}

export default EventsList
