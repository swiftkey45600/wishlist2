import { createGift } from "../repositories/giftRepository"
import api from "../services/api"

export const useRecommendationMocks = import.meta.env.DEV
    && import.meta.env.VITE_RECOMMENDATION_MOCKS === "true"

export async function getRecommendations(eventId) {
    if (!useRecommendationMocks) {
        const { data } = await api.get(`/events/${eventId}/recommendations`)
        return data
    }
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
