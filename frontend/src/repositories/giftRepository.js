import api from "../services/api"

export async function fetchGift(giftId) {
  const response = await api.get(`/gifts/${giftId}`)
  return response.data
}

export async function fetchGiftsByEvent(eventId) {
  const response = await api.get(`/events/${eventId}/gifts`)
  return response.data
}

export async function createGift(giftData) {
  const response = await api.post("/gifts/", giftData)
  return response.data
}

export async function updateGiftStatus(giftId, status) {
  const response = await api.patch(`/gifts/${giftId}/status`, null, {
    params: { status }
  })
  return response.data
}

export async function updateGift(giftId, data) {
  const response = await api.patch(`/gifts/${giftId}`, data)
  return response.data
}

export async function reserveGift(giftId, reserverName, isAnonymous = false) {
  const response = await api.post("/reservations/", {
    gift_id: giftId,
      reserver_name: reserverName,
      is_anonymous: isAnonymous
    })

  return response.data
}

export async function unreserveGift(reservationId) {
  await api.delete(`/reservations/${reservationId}`)
}

export async function deleteGift(giftId) {
  await api.delete(`/gifts/${giftId}`)
}
