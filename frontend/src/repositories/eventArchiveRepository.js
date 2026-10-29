import api from "../services/api"

export const eventArchiveEnabled = true

export async function changeEventArchive(eventId, archived) {
    const response = await api.patch(`/events/${eventId}/${archived ? "archive" : "restore"}`)
    return response.data.event
}

export async function copyEvent(eventId, title, eventDate, durationDays) {
    const response = await api.post(`/events/${eventId}/copy`, { title, event_date: eventDate || null, ...(durationDays != null ? { duration_days: durationDays } : {}) })
    return response.data.event
}
