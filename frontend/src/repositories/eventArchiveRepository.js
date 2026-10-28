import api from "../services/api"

// Enable when the S8.2 backend is available.
export const eventArchiveEnabled = import.meta.env.VITE_EVENT_ARCHIVE_ENABLED === "true"

export async function changeEventArchive(eventId, archived) {
    const response = await api.patch(`/events/${eventId}/${archived ? "archive" : "restore"}`)
    return response.data.event
}

export async function copyEvent(eventId, title, eventDate) {
    const response = await api.post(`/events/${eventId}/copy`, { title, event_date: eventDate || null })
    return response.data.event
}
