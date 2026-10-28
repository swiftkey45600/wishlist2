import { useCallback, useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"

import "./HomePage.css"
import "../../styles/common.css"

import { eventArchiveEnabled } from "../../repositories/eventArchiveRepository"
import { getEvents, createEvent } from "../../application/eventApplication"

import Header from "../../components/Header/Header"
import Sidebar from "../../components/Sidebar/Sidebar"
import CreateEventForm from "../../components/Events/CreateEventForm/CreateEventForm"
import EventsList from "../../components/Events/EventsList/EventsList"

function HomePage() {
  const navigate = useNavigate()
  const [events, setEvents] = useState([])
  const [archiveTab, setArchiveTab] = useState(false)
  const [giftStats, setGiftStats] = useState({ total: 0, reserved: 0 })
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [error, setError] = useState(null)
  const [eventsLoading, setEventsLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function loadEvents() {
      setEventsLoading(true)
      setError(null)
      try {
        const data = await getEvents(eventArchiveEnabled ? (archiveTab ? "archived" : "active") : undefined)
        if (!cancelled) setEvents(data)
      } catch {
        if (!cancelled) setError("Не удалось загрузить события. Обновите страницу.")
      } finally {
        if (!cancelled) setEventsLoading(false)
      }
    }

    loadEvents()
    return () => { cancelled = true }
  }, [archiveTab])


  async function handleCreateEvent(eventData) {
    setError(null)
    const createdEvent = await createEvent(eventData)

    if (createdEvent) {
      if (eventArchiveEnabled && archiveTab) setArchiveTab(false)
      else setEvents((currentEvents) => [...currentEvents, createdEvent])
      setIsCreateOpen(false)
      return true
    } else {
      setError("Не удалось создать событие")
      return false
    }
  }

  const visibleEvents = events

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

          {eventArchiveEnabled && <div className="event-archive-tabs">
            <button className="btn secondary" type="button" aria-pressed={!archiveTab} onClick={() => setArchiveTab(false)}>Активные</button>
            <button className="btn secondary" type="button" aria-pressed={archiveTab} onClick={() => setArchiveTab(true)}>Архив</button>
          </div>}
          {eventsLoading && <p role="status">Загружаем события...</p>}
          {eventArchiveEnabled && !eventsLoading && !error && visibleEvents.length === 0 && <p>{archiveTab ? "В архиве пока нет событий." : "Активных событий пока нет."}</p>}
          {!eventsLoading && !error && <EventsList
            events={visibleEvents}
            onOpenEvent={handleOpenEvent}
            onGiftsLoaded={handleGiftsLoaded}
          />}
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
