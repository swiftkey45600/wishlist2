import { useEffect, useState } from "react"

import "./HomePage.css"
import "../../Styles/common.css"

import { getEvents, createEvent, deleteEvent } from "../../application/eventApplication"

import Sidebar from "../../components/Sidebar/Sidebar"
import CreateEventForm from "../../components/Events/CreateEventForm/CreateEventForm"
import EventsList from "../../components/Events/EventsList/EventsList"

function HomePage() {
  const [events, setEvents] = useState([])

  useEffect(() => {
    async function loadEvents() {
      const data = await getEvents()
      setEvents(data)
    }

    loadEvents()
  }, [])


  async function handleCreateEvent(title, description, place, date) {
    const createdEvent = await createEvent({
      title,
      description,
      place,
      date
    })

    setEvents([...events, createdEvent])
  }

  async function handleDeleteEvent(eventId) {
    await deleteEvent(eventId)

    setEvents(events.filter(event => event.id !== eventId))
  }


  return (
    <div className="page-layout">
      <Sidebar />

      <div className="page-content">
        <div className="page-header">
            <h1>Мои события</h1>
            <p>Создавайте свои события и управляйте ими</p>
        </div>

        <CreateEventForm onCreateEvent={handleCreateEvent} />

        <EventsList 
          events={events}
          onDeleteEvent={handleDeleteEvent}
        />
      </div>
    </div>
  )
}

export default HomePage
