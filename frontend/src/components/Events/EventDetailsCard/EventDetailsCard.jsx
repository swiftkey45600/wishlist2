import "./EventDetailsCard.css"

function EventDetailsCard() {
    return (
        <div className="event-details-card">
            <img className="event-image" src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR1LrGiVbVaK4i8yF7DomI8kN1j1mQNM2GqnA&s"/>

            <div className="event-info">
                <h1>День Рождения Антонио</h1>

                <p>Уютно посидим :)</p>

                <div className="event-meta">
                    <span>📆 31.01.2027</span>

                    <span>🕒 18:00</span>

                    <span>📍 Доски</span>
                </div>
            </div>
        </div>
    )
}

export default EventDetailsCard
