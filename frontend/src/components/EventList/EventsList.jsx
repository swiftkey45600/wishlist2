import "./EventsList.css"
import EventCard from "../EventCard/EventCard"

function EventsList({ events, onDeleteEvent }) {
    return (
        <div className="events-list">
			<h2>Список событий</h2>
			{
				events.map((event) => 
					<EventCard 
					key={event.id}
					id={event.id}
					title={event.title}
					description={event.description}
					place={event.place}
					date={event.event_date}
					onDeleteEvent={onDeleteEvent}
					/>
				)
			}
        </div>
    )
}

export default EventsList
