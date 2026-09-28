import "./GiftCard.css"

function GiftCard({ gift, onToggleStatus, onDelete, onMarkBought, onEdit }) {
    return (
        <div className="gift-card">
            <div className="gift-card-main">
                <img
                    className="gift-image"
                    src={gift.picture_url || "https://via.placeholder.com/120x120?text=Gift"}
                    alt={gift.title}
                />
                <div className="gift-card-info">
                    <h3>{gift.title}</h3>
                    <p className="gift-description">{gift.description || "Описание подарка пока не добавлено."}</p>
                    <strong>{gift.price} ₽</strong>
                </div>
                <div className="gift-card-right">
                    <span className={`gift-status ${gift.status}`}>{gift.status}</span>
                    {onToggleStatus && (
                        <button
                            className="gift-secondary-button"
                            onClick={() => onToggleStatus(gift)}
                        >
                            {gift.status === "available"
                                ? "Забронировать"
                                : gift.status === "bought"
                                    ? "Отменить"
                                    : "Отменить"}
                        </button>
                    )}
                    {gift.status === "reserved" && onMarkBought && (
                        <button
                            className="gift-secondary-button"
                            onClick={() => onMarkBought(gift.id)}
                        >
                            Куплено
                        </button>
                    )}
                </div>
            </div>

            <div className="gift-card-footer">
                {gift.marketplace_url ? (
                    <a className="gift-marketplace" href={gift.marketplace_url} target="_blank" rel="noopener noreferrer">Открыть товар ↗</a>
                ) : <span className="gift-marketplace">Маркетплейс не указан</span>}
                <div className="gift-actions">
                    {onEdit && <button className="gift-secondary-button" onClick={() => onEdit(gift)}>Изменить</button>}
                    {onDelete && <button className="gift-danger-button" onClick={() => onDelete(gift.id)}>Удалить</button>}
                </div>
            </div>
        </div>
    )
}

export default GiftCard
