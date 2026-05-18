import "./Sidebar.css"

function Sidebar() {
  return (
    <div className="sidebar">
      <div className="sidebar-top">
        <h1>Wishlist</h1>

        <div className="sidebar-menu">
          <div className="sidebar-item active">
            Мои события
          </div>

          <div className="sidebar-item">
            Профиль
          </div>
        </div>
      </div>

      <div className="sidebar-bottom">
          <div className="sidebar-profile">
              John Doe
          </div>
      </div>
    </div>
  )
}

export default Sidebar
