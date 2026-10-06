export const useGuestReservationMocks = import.meta.env.DEV
    && import.meta.env.VITE_GUEST_RESERVATION_MOCKS === "true"

export async function getGuestReservationGifts(token, gifts) {
    if (!useGuestReservationMocks) return gifts

    const { getMockReservationGifts } = await import("../mocks/mockGuestReservations")
    return getMockReservationGifts(token, gifts)
}

export async function changeGuestReservation(token, gift, { name, secretWord }) {
    if (!useGuestReservationMocks) {
        throw new Error("Бронь без аккаунта пока недоступна. Войдите, чтобы забронировать подарок.")
    }

    const { reserveMockGift, cancelMockReservation } = await import("../mocks/mockGuestReservations")
    return gift.status === "available"
        ? reserveMockGift(token, gift, name, secretWord)
        : cancelMockReservation(token, gift, secretWord)
}
