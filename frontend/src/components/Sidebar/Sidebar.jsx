import { NavLink } from "react-router-dom"

import "./Sidebar.css"

function Sidebar({ activeSection }) {
  return (
    <aside className="sidebar">
      <div className="label">Навигация</div>
      <div className="nav">
        <NavLink
          to='/'
          end
          className={({ isActive }) =>
          isActive || activeSection === "events"
            ? "sidebar-link active"
            : "sidebar-link"
          }
        >
          Мои события
        </NavLink>

        <NavLink
          to='/presents'
          className={({ isActive }) => isActive ? "sidebar-link active" : "sidebar-link"}
        >
          Мои подарки
        </NavLink>

        <button type="button" className="sidebar-link future" disabled>
          Публичные события
        </button>

      </div>

      <div className="label" style={{ marginTop: "27px" }}>Аккаунт</div>
      <div className="nav">

        <NavLink
          to='/profile'
          className={({ isActive }) =>
          isActive
            ? "sidebar-link active"
            : "sidebar-link"
          }
        >
          Профиль
        </NavLink>

        <button type="button" className="sidebar-link future" disabled>
          Настройки
        </button>

      </div>
    </aside>
  )
}

export default Sidebar
