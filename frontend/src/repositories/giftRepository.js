import api from "../services/api"

export async function fetchGift(giftId) {
  const response = await api.get(`/gifts/${giftId}`)
  return response.data
}

export async function fetchGiftsByEvent(eventId, showReservations = false) {
  const response = await api.get(`/events/${eventId}/gifts`, { params: { show_reservations: showReservations } })
  return response.data
}

export async function createGift(giftData) {
  const response = await api.post("/gifts/", giftData)
  return response.data
}

export async function updateGift(giftId, data) {
  const response = await api.patch(`/gifts/${giftId}`, data)
  return response.data
}

export async function updatePublicGiftReservation(token, giftId, isReserved) {
  const response = await api.patch(`/events/public/${token}/gifts/${giftId}/reservation`, {
    is_reserved: isReserved
  })
  return response.data
}

export async function reserveGift(giftId, isAnonymous = false, publicToken) {
  const response = await api.post("/reservations/", {
    gift_id: giftId,
    public_token: publicToken,
    is_anonymous: isAnonymous
  })
  return response.data
}

export async function unreserveGift(reservationId) {
  const response = await api.delete(`/reservations/${reservationId}`)
  return response.data
}

export async function deleteGift(giftId) {
  await api.delete(`/gifts/${giftId}`)
}

export async function setGiftReceived(giftId, received) {
  const response = await api.patch(`/gifts/${giftId}/received`, { received })
  return response.data
}

export async function carryGift(giftId, eventId) {
  const response = await api.post(`/gifts/${giftId}/carry`, { event_id: eventId })
  return response.data
}
