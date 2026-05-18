import { useEffect, useState } from "react"

import "./App.css"

import { getEvents, createEvent, deleteEvent } from "./application/eventApplication"

import Sidebar from "./components/Sidebar/Sidebar"
import Header from "./components/Header/Header"
import CreateEventForm from "./components/CreateEventForm/CreateEventForm"
import EventsList from "./components/EventList/EventsList"

function App() {
  // TODO архитектурная прослойка (словарь) - посмотреть гайд

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
    <div className="app-layout">
      <Sidebar />

      <div className="main-content">
        <Header />

        <CreateEventForm onCreateEvent={handleCreateEvent} />

        <EventsList 
          events={events}
          onDeleteEvent={handleDeleteEvent}
        />
      </div>
    </div>
  )
}

export default App