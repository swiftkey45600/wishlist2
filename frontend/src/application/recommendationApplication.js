import { createGift } from "../repositories/giftRepository"

export const useRecommendationMocks = import.meta.env.DEV
    && import.meta.env.VITE_RECOMMENDATION_MOCKS === "true"

export async function getRecommendations(eventId) {
    if (!useRecommendationMocks) return []
    const { fetchMockRecommendations } = await import("../mocks/mockRecommendations")
    return fetchMockRecommendations(eventId)
}

export function isRecommendedGiftAdded(recommendation, gifts = []) {
    const recommendationTitle = String(recommendation?.title || "").trim().toLowerCase()
    const recommendationUrl = String(recommendation?.marketplace_url || "").trim().toLowerCase()

    return gifts.some(gift => {
        const giftTitle = String(gift?.title || "").trim().toLowerCase()
        const giftUrl = String(gift?.marketplace_url || "").trim().toLowerCase()

        return (
            (recommendationUrl && giftUrl && giftUrl === recommendationUrl)
            || (recommendationTitle && giftTitle && giftTitle === recommendationTitle)
        )
    })
}

export async function addRecommendedGift(eventId, recommendation) {
    // Копируем только данные товара, без чужих ID, брони и тегов события.
    return createGift({
        event_id: Number(eventId),
        title: recommendation.title,
        price: recommendation.price,
        description: recommendation.description || null,
        picture_url: recommendation.picture_url || null,
        marketplace_url: recommendation.marketplace_url || null,
        status: "available"
    })
}
