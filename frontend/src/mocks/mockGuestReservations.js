// Только локальная демонстрация. После перезагрузки страницы состояние сбрасывается.
const reservations = new Map()

function reservationKey(token, giftId) {
    return `${token}:${giftId}`
}

async function hashWord(word) {
    const bytes = new TextEncoder().encode(word)
    const hash = await crypto.subtle.digest("SHA-256", bytes)
    return Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2, "0")).join("")
}

function waitForResponse() {
    return new Promise(resolve => setTimeout(resolve, 300))
}

export function getMockReservationGifts(token, gifts) {
    return gifts.map(gift => {
        const reservation = reservations.get(reservationKey(token, gift.id))
        return reservation ? { ...gift, status: reservation.status } : gift
    })
}

export async function reserveMockGift(token, gift, name, secretWord) {
    if (!name.trim() || !secretWord.trim()) throw new Error("Введите имя и секретное слово")
    const secretHash = await hashWord(secretWord)
    await waitForResponse()
    const key = reservationKey(token, gift.id)
    const status = reservations.get(key)?.status ?? gift.status
    if (status !== "available") throw new Error("Подарок уже занят. Выберите другой.")

    reservations.set(key, { status: "reserved", secretHash })
    return { ...gift, status: "reserved" }
}

export async function cancelMockReservation(token, gift, secretWord) {
    const secretHash = await hashWord(secretWord)
    await waitForResponse()
    const key = reservationKey(token, gift.id)
    const reservation = reservations.get(key)
    if (!reservation || reservation.status !== "reserved" || reservation.secretHash !== secretHash) {
        throw new Error("Секретное слово не подошло или эта бронь создана вне деморежима.")
    }

    reservations.set(key, { status: "available" })
    return { ...gift, status: "available" }
}
