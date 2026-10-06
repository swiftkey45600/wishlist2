import { createGift } from "../repositories/giftRepository"

export const useRecommendationMocks = import.meta.env.DEV
    && import.meta.env.VITE_RECOMMENDATION_MOCKS === "true"

export async function getRecommendations() {
    if (!useRecommendationMocks) return []
    const { fetchMockRecommendations } = await import("../mocks/mockRecommendations")
    return fetchMockRecommendations()
}

export function isRecommendedGiftAdded(recommendation, gifts) {
    return gifts.some(gift =>
        (recommendation.marketplace_url && gift.marketplace_url === recommendation.marketplace_url)
        || gift.title?.trim().toLowerCase() === recommendation.title.trim().toLowerCase()
    )
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
