import api from "../services/api"

export async function reserveGuestGift(token, giftId, name, secretWord) {
    const response = await api.post(`/events/public/${token}/gifts/${giftId}/reservation`, {
        name,
        secret_word: secretWord
    })
    return response.data
}

export async function cancelGuestReservation(token, giftId, secretWord) {
    await api.delete(`/events/public/${token}/gifts/${giftId}/reservation`, {
        data: { secret_word: secretWord }
    })
}
