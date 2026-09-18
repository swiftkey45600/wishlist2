import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"

import "./HomePage.css"
import "../../Styles/common.css"

import { getEvents, createEvent, deleteEvent } from "../../application/eventApplication"

import Header from "../../components/Header/Header"
import Sidebar from "../../components/Sidebar/Sidebar"
import CreateEventForm from "../../components/Events/CreateEventForm/CreateEventForm"
import EventsList from "../../components/Events/EventsList/EventsList"

function HomePage() {
  const navigate = useNavigate()
  const [events, setEvents] = useState([])
  const [giftStats, setGiftStats] = useState({ total: 0, reserved: 0 })
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [shareToast, setShareToast] = useState("")

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

    if (createdEvent) {
      setEvents((currentEvents) => [...currentEvents, createdEvent])
      setIsCreateOpen(false)
    }
  }

  async function handleDeleteEvent(eventId) {
    await deleteEvent(eventId)

    setEvents(events.filter(event => event.id !== eventId))
  }

  function handleOpenEvent(eventId) {
    navigate(`/events/${eventId}`)
  }

  function handleGiftsLoaded(giftsByEvent) {
    const allGifts = Object.values(giftsByEvent).flat()

    setGiftStats({
      total: allGifts.length,
      reserved: allGifts.filter((gift) => gift.status === "reserved").length
    })
  }

  async function handleShareEvent(event) {
    const shareLink = event.public_token
      ? `${window.location.origin}/share/${event.public_token}`
      : `${window.location.origin}/events/${event.id}`

    try {
      await navigator.clipboard.writeText(shareLink)
      setShareToast("Ссылка скопирована")
      window.setTimeout(() => setShareToast(""), 2200)
    } catch (shareError) {
      console.error("Не удалось скопировать ссылку", shareError)
      setShareToast("Не удалось скопировать ссылку")
      window.setTimeout(() => setShareToast(""), 2200)
    }
  }


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
            onDeleteEvent={handleDeleteEvent}
            onOpenEvent={handleOpenEvent}
            onShareEvent={handleShareEvent}
            onGiftsLoaded={handleGiftsLoaded}
          />
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

      {shareToast && <div className="home-toast">{shareToast}</div>}
    </div>
  )
}

export default HomePage
