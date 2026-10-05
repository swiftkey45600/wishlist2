import api from "../services/api"

export async function fetchEventTags(eventId) {
    const response = await api.get(`/events/${eventId}/tags`)
    return response.data
}

export async function createEventTag(eventId, name) {
    const response = await api.post(`/events/${eventId}/tags`, { name })
    return response.data
}

export async function updateEventTag(tagId, name) {
    const response = await api.patch(`/tags/${tagId}`, { name })
    return response.data
}

export async function deleteEventTag(tagId) {
    await api.delete(`/tags/${tagId}`)
}
