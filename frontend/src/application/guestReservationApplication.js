import { reserveGuestGift, cancelGuestReservation } from "../repositories/guestReservationRepository"

export async function changeGuestReservation(token, gift, { name, secretWord }) {
    try {
        if (gift.status === "available") {
            const reservation = await reserveGuestGift(token, gift.id, name.trim(), secretWord)
            return { ...gift, status: "reserved", reservation_id: reservation.id }
        }
        await cancelGuestReservation(token, gift.id, secretWord)
        return { ...gift, status: "available", reservation_id: null }
    } catch (error) {
        const messages = {
            403: "Секретное слово не подошло или эта бронь создана через аккаунт.",
            404: "Подарок или бронь не найдены. Обновите страницу.",
            409: "Подарок уже занят. Обновите страницу.",
            422: "Проверьте имя и секретное слово.",
            429: "Слишком много попыток. Подождите и попробуйте позже."
        }
        throw new Error(messages[error.response?.status] || "Не удалось изменить бронь. Попробуйте ещё раз.", { cause: error })
    }
}
