import { useEffect, useState } from "react"
import { Link, NavLink } from "react-router-dom"
import { CalendarDays, ChevronLeft, ChevronRight, Gift, Sparkles, UserRound } from "lucide-react"
import { getEvents } from "../../application/eventApplication"
import "./Sidebar.css"

function Sidebar({ activeSection, events: providedEvents }) {
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem("sidebarCollapsed") === "true")
  const [loadedEvents, setLoadedEvents] = useState([])
  const [eventsReady, setEventsReady] = useState(false)

  useEffect(() => {
    if (providedEvents || !localStorage.getItem("accessToken")) return
    let active = true
    getEvents("active").then(events => {
      if (active) { setLoadedEvents(events); setEventsReady(true) }
    }).catch(() => { if (active) setEventsReady(false) })
    return () => { active = false }
  }, [providedEvents])

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const nextEvent = (providedEvents || loadedEvents)
    .filter(event => event.status !== "archived" && event.event_date && !Number.isNaN(new Date(event.event_date).getTime()) && new Date(event.event_date) >= today)
    .sort((a, b) => new Date(a.event_date) - new Date(b.event_date))[0]

  function toggleSidebar() {
    setCollapsed(value => {
      localStorage.setItem("sidebarCollapsed", String(!value))
      return !value
    })
  }

  return (
    <aside className={`sidebar${collapsed ? " sidebar--collapsed" : ""}`}>
      <div className="sidebar-heading">
        <p className="sidebar-label">ВАШЕ ПРОСТРАНСТВО</p>
        <button className="sidebar-toggle" type="button" onClick={toggleSidebar}
          aria-label={collapsed ? "Развернуть меню" : "Свернуть меню"} aria-expanded={!collapsed}>
          {collapsed ? <ChevronRight size={17} /> : <ChevronLeft size={17} />}
        </button>
      </div>
      <nav className="sidebar-nav" aria-label="Основная навигация">
        <NavLink to="/" end title="Мои события" aria-label="Мои события"
          className={({ isActive }) => isActive || activeSection === "events" ? "sidebar-link active" : "sidebar-link"}>
          <CalendarDays size={19} /><span>Мои события</span>
        </NavLink>
        <NavLink to="/presents" title="Мои подарки" aria-label="Мои подарки"
          className={({ isActive }) => isActive ? "sidebar-link active" : "sidebar-link"}>
          <Gift size={19} /><span>Мои подарки</span>
        </NavLink>
        <NavLink to="/profile" title="Профиль" aria-label="Профиль"
          className={({ isActive }) => isActive ? "sidebar-link active" : "sidebar-link"}>
          <UserRound size={19} /><span>Профиль</span>
        </NavLink>
      </nav>
      {!collapsed && (providedEvents || eventsReady) && <div className="sidebar-upcoming">
        <div className="sidebar-upcoming-label"><Sparkles size={14} /> БЛИЖАЙШЕЕ СОБЫТИЕ</div>
        {nextEvent ? <Link to={`/events/${nextEvent.id}`} className="sidebar-upcoming-link">
          <strong>{nextEvent.title}</strong>
          <span>{new Date(nextEvent.event_date).toLocaleDateString("ru-RU", { day: "numeric", month: "long" })} →</span>
        </Link> : <p>Здесь появится ваше ближайшее событие.</p>}
      </div>}
    </aside>
  )
}

export default Sidebar
