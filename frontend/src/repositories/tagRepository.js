import api from "../services/api"

export async function fetchEventTags(eventId) {
    const response = await api.get(`/events/${eventId}/tags`)
    return response.data
}

export async function createEventTag(eventId, name) {
    const response = await api.post(`/events/${eventId}/tags`, { name })
    return response.data
}

export async function updateEventTag(eventId, tagId, name) {
    const response = await api.patch(`/events/${eventId}/tags/${tagId}`, { name })
    return response.data
}

export async function deleteEventTag(eventId, tagId) {
    await api.delete(`/events/${eventId}/tags/${tagId}`)
}
