import { NavLink } from "react-router-dom"

import "./Sidebar.css"

function Sidebar() {
  const user = JSON.parse(localStorage.getItem("user") || "null")
  return (
    <div className="sidebar">
      <div className="sidebar-top">
        <h1>Wishlist</h1>

        <div className="sidebar-menu">

          <NavLink
            to="/"
            className={({ isActive }) =>
              isActive
                ? "sidebar-link active"
                : "sidebar-link"
            }
          >
            Мои события
          </NavLink>

          <NavLink
            to="/profile"
            className={({ isActive }) =>
              isActive
                ? "sidebar-link active"
                : "sidebar-link"
            }
          >
            Профиль
          </NavLink>

        </div>
      </div>

      <div className="sidebar-bottom">
          <div className="sidebar-profile">
            {user ? user.name : "Гость"}
          </div>
      </div>
    </div>
  )
}

export default Sidebar
