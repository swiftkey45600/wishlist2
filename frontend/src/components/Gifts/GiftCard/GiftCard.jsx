import "./GiftCard.css"
import GiftImage from "../GiftImage/GiftImage"
import GiftQuestions from "../GiftQuestions/GiftQuestions"
import { getGiftStatusLabel } from "../giftStatus"
import GiftFundraising from "../GiftFundraising/GiftFundraising"
import { getGiftPriorityLabel } from "../giftPriority"

function marketplaceLink(value) {
    try {
        const url = new URL(value)
        return ["http:", "https:"].includes(url.protocol) ? url.toString() : ""
    } catch {
        return ""
    }
}

function GiftCard({ gift, onToggleStatus, onDelete, onMarkBought, onEdit, hideReservationDetails = false,
    publicToken, isOwner = false, onGiftChange }) {
    const hideStatus = hideReservationDetails && ["reserved", "bought"].includes(gift.status)
    const productUrl = marketplaceLink(gift.marketplace_url)

    return (
        <div className="gift-card">
            <div className="gift-card-main">
                <GiftImage
                    gift={gift}
                    className="gift-image"
                    fallbackClassName="gift-image gift-image-fallback"
                />
                <div className="gift-card-info">
                    <div className="gift-card-title">
                        <h3>{gift.title}</h3>
                        {gift.priority === "high" && (
                            <span className="gift-priority-badge">{getGiftPriorityLabel(gift.priority)}</span>
                        )}
                        {gift.tags?.length > 0 && (
                            <div className="gift-tag-list">
                                {gift.tags.slice(0, 3).map(tag => (
                                    <span className="gift-tag" key={tag.id}>{tag.name}</span>
                                ))}
                                {gift.tags.length > 3 && (
                                    <span className="gift-tag-overflow">
                                        <button
                                            type="button"
                                            className="gift-tag gift-tag-more"
                                            aria-label={`${gift.tags.length - 3} скрытых тегов`}
                                            aria-describedby={`gift-hidden-tags-${gift.id}`}
                                        >
                                            +{gift.tags.length - 3}
                                        </button>
                                        <span className="gift-hidden-tags" id={`gift-hidden-tags-${gift.id}`} role="tooltip">
                                            {gift.tags.slice(3).map(tag => (
                                                <span className="gift-hidden-tag" key={tag.id}>{tag.name}</span>
                                            ))}
                                        </span>
                                    </span>
                                )}
                            </div>
                        )}
                    </div>
                    <p className="gift-description">{gift.description || "Описание подарка пока не добавлено."}</p>
                    <strong>{gift.price} ₽</strong>
                </div>
                <div className="gift-card-right">
                    {!hideStatus && (
                        <span className={`gift-status ${gift.status}`}>{getGiftStatusLabel(gift.status)}</span>
                    )}
                    {onToggleStatus && !gift.contribution_goal && (
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

            {gift.contribution_goal > 0 && <GiftFundraising
                gift={gift}
                publicToken={publicToken}
                isOwner={isOwner}
                hideContributionDetails={hideReservationDetails && isOwner}
                onGiftChange={onGiftChange}
            />}

            {publicToken && <GiftQuestions token={publicToken} giftId={gift.id} isOwner={isOwner} />}

            <div className="gift-card-footer">
                {productUrl && (
                    <a className="gift-marketplace" href={productUrl} target="_blank" rel="noopener noreferrer">Открыть товар ↗</a>
                )}
                <div className="gift-actions">
                    {onEdit && <button className="gift-secondary-button" onClick={() => onEdit(gift)}>Изменить</button>}
                    {onDelete && <button className="gift-danger-button" onClick={() => onDelete(gift.id)}>Удалить</button>}
                </div>
            </div>
        </div>
    )
}

export default GiftCard
