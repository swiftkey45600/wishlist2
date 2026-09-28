import { useCallback, useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"

import "./HomePage.css"
import "../../Styles/common.css"

import { getEvents, createEvent } from "../../application/eventApplication"

import Header from "../../components/Header/Header"
import Sidebar from "../../components/Sidebar/Sidebar"
import CreateEventForm from "../../components/Events/CreateEventForm/CreateEventForm"
import EventsList from "../../components/Events/EventsList/EventsList"

function HomePage() {
  const navigate = useNavigate()
  const [events, setEvents] = useState([])
  const [giftStats, setGiftStats] = useState({ total: 0, reserved: 0 })
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function loadEvents() {
      const data = await getEvents()
      setEvents(data)
    }

    loadEvents()
  }, [])


  async function handleCreateEvent(title, description, place, eventDate) {
    setError(null)
    const createdEvent = await createEvent({
      title,
      description,
      place,
      event_date: eventDate
    })

    if (createdEvent) {
      setEvents((currentEvents) => [...currentEvents, createdEvent])
      setIsCreateOpen(false)
    } else {
      setError("Не удалось создать событие")
    }
  }

  function handleOpenEvent(eventId) {
    navigate(`/events/${eventId}`)
  }

  const handleGiftsLoaded = useCallback((giftsByEvent) => {
    const allGifts = Object.values(giftsByEvent).flat()

    setGiftStats({
      total: allGifts.length,
      reserved: allGifts.filter((gift) => gift.status === "reserved").length
    })
  }, [])

  return (
    <div className="shell">
      <Header />

      <div className="body">
        <Sidebar />

        <main>
          <div className="heading">
            <div>
              <h1>Мои события</h1>
              <div className="muted">Списки желаний для ваших событий</div>
            </div>

            <button
              className="btn primary"
              onClick={() => setIsCreateOpen(true)}
            >
              ＋ Создать событие
            </button>
          </div>

          <div className="stats">
            <div className="stat">
              <small>Мои события</small>
              <strong>{events.length}</strong>
            </div>

            <div className="stat">
              <small>Подарки</small>
              <strong>{giftStats.total}</strong>
            </div>
            <div className="stat">
              <small>Забронировано</small>
              <strong>{giftStats.reserved}</strong>
            </div>
          </div>

          <div className="section">
            <h2>События</h2>
            <span className="muted">Ваши события</span>
          </div>

          <EventsList
            events={events}
            onOpenEvent={handleOpenEvent}
            onGiftsLoaded={handleGiftsLoaded}
          />
          {error && <p className="error-text">{error}</p>}
        </main>
      </div>

      {isCreateOpen && (
        <div
          className="create-modal"
          onClick={(event) => {
            if (event.target === event.currentTarget) {
              setIsCreateOpen(false)
            }
          }}
        >
          <div className="create-dialog">
            <CreateEventForm
              onCreateEvent={handleCreateEvent}
              onCancel={() => setIsCreateOpen(false)}
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default HomePage
