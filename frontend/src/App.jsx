import "./App.css"
import { useState } from "react"
import Sidebar from "./components/Sidebar/Sidebar"
import Header from "./components/Header/Header"
import CreateEventForm from "./components/CreateEventForm/CreateEventForm"
import EventsList from "./components/EventList/EventsList"

function App() {
  // TODO архитектурная прослойка (словарь) - посмотреть гайд
  // TODO папки со стилями!
  const [events, setEvents] = useState([
    {
      title: "ДР Антонио",
      description: "Уютно посидим :)",
      place: "Доски",
      date: "31.01 12:52"
    },

    {
      title: "Внезапный бар в пятницу",
      description: "После матана",
      place: "Контакт Бар",
      date: "17.05 18:00"
    }
  ])

  function handleCreateEvent(title, description, place, date) {
    const newEvent = {
      title,
      description,
      place,
      date
    }

    setEvents([...events, newEvent])
  }

  return (
    <div className="app-layout">
      <Sidebar />

      <div className="main-content">
        <Header />

        <CreateEventForm onCreateEvent={handleCreateEvent} />

        <EventsList events={events} />
      </div>
    </div>
  )
}

export default App