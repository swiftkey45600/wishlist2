import "./ProfileCard.css"

function ProfileCard({ user, onEditProfile }) {
    return (
        <div className="profile-card">
            <button className="edit-profile-button" onClick={() => onEditProfile(user)}>
                Изменить профиль      
            </button>

            <div className="profile-avatar">
                <img src="https://via.placeholder.com/96" alt="Avatar" />
            </div>

            <div className="profile-info">
                <h2>{user?.name || "Пользователь"}</h2>
                <p>{user?.login || "Не задан"}</p>
                {user?.birthday && <p>Дата рождения: {user.birthday}</p>}
                {user?.gender && <p>Пол: {user.gender}</p>}
            </div>
        </div>
    )
}

export default ProfileCard
