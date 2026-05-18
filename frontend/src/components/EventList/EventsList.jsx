import "./EventsList.css"
import EventCard from "../EventCard/EventCard"

function EventsList({ events }) {
    return (
        <div className="events-list">
			<h2>Список событий</h2>
			{
				events.map((event, index) => 
					<EventCard 
					key={index}
					title={event.title}
					description={event.description}
					place={event.place}
					date={event.date}
					/>
				)
			}
        </div>
    )
}

export default EventsList
