import "./ProfileCard.css"

function ProfileCard() {
    return (
        <div className="profile-card">
            <button className="edit-profile-button">
                Изменить профиль      
            </button>

            <div className="profile-avatar">
                <img></img>
            </div>

            <div className="profile-info">
                <h2>Арсений</h2>
                <p>arseniytyurin52@mail.com</p>
            </div>
        </div>
    )
}

export default ProfileCard
