import "./Header.css"

function Header() {
    const user = JSON.parse(localStorage.getItem("user") || "null")
    const initial = (user?.name || "П").charAt(0).toUpperCase()
    return (
        <header className="top">

            <div className="logo">
                <div className="mark">♡</div>
                Wishlist
            </div>

            <div className="user">
                <span>
                    {user ? user.name : "Гость"}
                </span>

                <div className="avatar">
                    {initial}
                </div>
            </div>

        </header>
    )
}

export default Header
