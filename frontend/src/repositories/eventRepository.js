import api from "../services/api"

export async function fetchEvents() {
    const response = await api.get("/events/")

    return response.data.events
}

export async function createEvent(eventData) {
    const response = await api.post("/events/", {
        title: eventData.title,
        description: eventData.description,
        event_date: eventData.date,
        place: eventData.place
    })

    return response.data.event
}

export async function deleteEvent(eventId) {
    await api.delete(`/events/${eventId}`)
}
