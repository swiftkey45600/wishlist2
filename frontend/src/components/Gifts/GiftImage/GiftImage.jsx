import { useState } from "react"
import { resolveImageUrl } from "../../../application/imageApplication"

const fallbackEmojis = ["🎁", "🌷", "🍰", "🎧", "📚", "🧸", "🎮", "☕", "✨", "🌿"]

function getFallbackEmoji(giftId) {
    const id = String(giftId ?? "")
    const hash = Array.from(id).reduce(
        (value, character) => (value * 31 + character.charCodeAt(0)) >>> 0,
        0,
    )
    return fallbackEmojis[hash % fallbackEmojis.length]
}

function GiftImage({ gift, className, fallbackClassName, alt = "" }) {
    const imageUrl = resolveImageUrl(gift.image_id, gift.picture_url || gift.image_url)
    const [failedImageUrl, setFailedImageUrl] = useState(null)

    if (imageUrl && failedImageUrl !== imageUrl) {
        return (
            <img
                className={className}
                src={imageUrl}
                alt={alt || gift.title}
                onError={() => setFailedImageUrl(imageUrl)}
            />
        )
    }

    return (
        <span className={fallbackClassName} role="img" aria-label={alt || gift.title}>
            {getFallbackEmoji(gift.id)}
        </span>
    )
}

export default GiftImage