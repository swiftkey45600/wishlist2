import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"

import "./HomePage.css"
import "../../Styles/common.css"

import { getEvents, createEvent, deleteEvent, editEvent } from "../../application/eventApplication"

import Sidebar from "../../components/Sidebar/Sidebar"
import CreateEventForm from "../../components/Events/CreateEventForm/CreateEventForm"
import EventsList from "../../components/Events/EventsList/EventsList"

function HomePage() {
  const navigate = useNavigate()
  const [events, setEvents] = useState([])

  useEffect(() => {
    async function loadEvents() {
      const data = await getEvents()
      setEvents(data)
    }

    loadEvents()
  }, [])


  async function handleCreateEvent(title, description, place, eventDate) {
    const createdEvent = await createEvent({
      title,
      description,
      place,
      event_date: eventDate
    })

    setEvents([...events, createdEvent])
  }

  async function handleDeleteEvent(eventId) {
    await deleteEvent(eventId)

    setEvents(events.filter(event => event.id !== eventId))
  }

  async function handleEditEvent(event) {
    const title = window.prompt("Название события", event.title)
    if (title === null) return

    const description = window.prompt("Описание события", event.description || "")
    if (description === null) return

    const place = window.prompt("Место события", event.place || "")
    if (place === null) return

    const updatedEvent = await editEvent(event.id, { title, description, place })
    if (updatedEvent) {
      setEvents(events.map(item => item.id === event.id ? updatedEvent : item))
    }
  }

  function handleOpenEvent(eventId) {
    navigate(`/events/${eventId}`)
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
          onOpenEvent={handleOpenEvent}
          onEditEvent={handleEditEvent}
        />
      </div>
    </div>
  )
}

export default HomePage
