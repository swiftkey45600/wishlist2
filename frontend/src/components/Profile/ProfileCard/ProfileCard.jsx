import "./ProfileCard.css"

function ProfileCard({ user }) {
    const initial = (user?.name || "П").charAt(0).toUpperCase()

    return (
        <div className="profile-hero">
            <div className="profile-avatar">{initial}</div>
            <div>
                <div className="profile-hero-name">{user?.name || "Пользователь"}</div>
                <div className="profile-hero-login">@{user?.login || "user"}</div>
            </div>
        </div>
    )
}

export default ProfileCard
