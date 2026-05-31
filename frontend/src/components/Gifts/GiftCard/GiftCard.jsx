import "./GiftCard.css"

function GiftCard({ gift }) {
    return (
        <div className="gift-card">
            <img className="gift-image" src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ4uA4xrGkOPyuOv8RRrX8k4UMJVlkhW-TshQ&s"/>
            <h3>{gift.title}</h3>

            <div className="gift-card-footer">
                <span>{gift.price} ₽</span>

                <div className="gift-actions">
                    <button className="edit-gift-button">
                        ✏️
                    </button>

                    <button className="delete-gift-button">
                        🗑️
                    </button>
                </div>
            </div>
        </div>
    )
}

export default GiftCard
