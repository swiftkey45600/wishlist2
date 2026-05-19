import { Link } from "react-router-dom"

import "./EventsList.css"

import EventCard from "../EventCard/EventCard"

function EventsList({ events, onDeleteEvent }) {
    return (
        <div className="events-list">
			<h2>Список событий</h2>
			{
				events.map((event) => 
					<Link key={event.id} to={`/events/${event.id}`}>
						<EventCard 
							key={event.id}
							id={event.id}
							title={event.title}
							description={event.description}
							place={event.place}
							date={event.event_date}
							onDeleteEvent={onDeleteEvent}
						/>
					</Link>
				)
			}
        </div>
    )
}

export default EventsList
