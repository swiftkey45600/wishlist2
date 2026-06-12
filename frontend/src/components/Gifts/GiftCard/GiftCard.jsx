import "./GiftCard.css"

function GiftCard({ gift, onToggleStatus, onDelete, onMarkBought, onEdit }) {
    const toggleText = gift.status === "available" ? "Занять" : "Снять бронь"

    return (
        <div className="gift-card">
            <img
                className="gift-image"
                src={gift.picture_url || "https://via.placeholder.com/300x200?text=No+Image"}
                alt={gift.title}
            />
            <h3>{gift.title}</h3>
            
            {gift.marketplace_url && (
                <a
                    href={gift.marketplace_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="marketplace-link"
                >
                    Посмотреть на маркетплейсе →
                </a>
            )}

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

                    {gift.status === "reserved" && onMarkBought && (
                        <button
                            className="bought-button"
                            onClick={() => onMarkBought(gift.id)}
                        >
                            Куплено ✓
                        </button>
                    )}

                    {onEdit && (
                        <button className="edit-gift-button" onClick={() => onEdit(gift)}>
                            ✏️
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
