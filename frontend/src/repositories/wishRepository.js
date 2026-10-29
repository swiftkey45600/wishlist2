import api from "../services/api"

export async function getWishes() { return (await api.get("/wishes/")).data }
export async function createWish(data) { return (await api.post("/wishes/", data)).data }
export async function editWish(id, data) { return (await api.put(`/wishes/${id}`, data)).data }
export async function removeWish(id) { await api.delete(`/wishes/${id}`) }
export async function receiveWish(id, received) { return (await api.patch(`/wishes/${id}/received`, { received })).data }
export async function addWishToEvent(id, eventId) { return (await api.post(`/wishes/${id}/events`, { event_id: eventId })).data }

export async function createWishShare(items) { return (await api.post("/wish-shares/", { items })).data }
export async function getWishShare(token) { return (await api.get(`/wish-shares/${encodeURIComponent(token)}`)).data }

export async function reserveSharedWish(token, position, data = {}) { return (await api.post(`/wish-shares/${encodeURIComponent(token)}/items/${position}/reservation`, data)).data }
export async function cancelSharedWish(token, position, data = {}) { return (await api.delete(`/wish-shares/${encodeURIComponent(token)}/items/${position}/reservation`, { data })).data }

export async function revokeWishShare(token) { await api.delete(`/wish-shares/${encodeURIComponent(token)}`) }
