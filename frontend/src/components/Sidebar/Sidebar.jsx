import { NavLink } from "react-router-dom"

import "./Sidebar.css"

function Sidebar({ activeSection }) {
  return (
    <aside className="sidebar">
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
      </div>

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
      </div>
    </aside>
  )
}

export default Sidebar
