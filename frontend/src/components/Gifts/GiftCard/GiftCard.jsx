import "./GiftCard.css"

function GiftCard({ gift, onToggleStatus, onDelete }) {
    const toggleText = gift.status === "available" ? "Занять" : "Снять бронь"

    return (
        <div className="gift-card">
            <img
                className="gift-image"
                src={gift.picture_url || "https://via.placeholder.com/300x200?text=No+Image"}
                alt={gift.title}
            />
            <h3>{gift.title}</h3>
            <p className="gift-status-label">Статус: {gift.status}</p>

            <div className="gift-card-footer">
                <span>{gift.price} ₽</span>

                <div className="gift-actions">
                    {onToggleStatus && (
                        <button
                            className="edit-gift-button"
                            onClick={() => onToggleStatus(gift)}
                        >
                            {toggleText}
                        </button>
                    )}

                    {onDelete && (
                        <button
                            className="delete-gift-button"
                            onClick={() => onDelete(gift.id)}
                        >
                            🗑️
                        </button>
                    )}
                </div>
            </div>
        </div>
    )
}

export default GiftCard
