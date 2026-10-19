import api from "../services/api"

export const useGuestReservationMocks = import.meta.env.DEV
    && import.meta.env.VITE_GUEST_RESERVATION_MOCKS === "true"

export async function getGuestReservationGifts(token, gifts) {
    if (!useGuestReservationMocks) return gifts

    const { getMockReservationGifts } = await import("../mocks/mockGuestReservations")
    return getMockReservationGifts(token, gifts)
}

export async function changeGuestReservation(token, gift, { name, secretWord }) {
    if (!useGuestReservationMocks) {
        const path = `/events/public/${encodeURIComponent(token)}/gifts/${gift.id}/reservation`
        try {
            if (gift.status === "available") {
                const { data } = await api.post(path, { name: name.trim(), secret_word: secretWord })
                return { ...gift, status: "reserved", reservation_id: data.id }
            }
            await api.delete(path, { data: { secret_word: secretWord } })
            return { ...gift, status: "available", reservation_id: null }
        } catch (error) {
            const messages = {
                403: "Неверное секретное слово или эта бронь создана через аккаунт.",
                404: "Подарок или бронь больше не найдены. Обновите страницу.",
                409: "Подарок уже забронирован. Обновите страницу.",
                422: "Проверьте имя и секретное слово (не более 72 байт).",
                429: "Слишком много попыток. Попробуйте через минуту."
            }
            throw new Error(messages[error.response?.status] || "Не удалось изменить бронь. Попробуйте ещё раз.", { cause: error })
        }
    }

    const { reserveMockGift, cancelMockReservation } = await import("../mocks/mockGuestReservations")
    return gift.status === "available"
        ? reserveMockGift(token, gift, name, secretWord)
        : cancelMockReservation(token, gift, secretWord)
}
