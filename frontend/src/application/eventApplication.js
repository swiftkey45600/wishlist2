import {
    fetchEvents,
    createEvent as createEventRepository,
    fetchUserEvents as fetchUserEventsRepository,
    fetchEvent as fetchEventRepository,
    deleteEvent as deleteEventRepository,
    updateEvent as updateEventRepository
} from "../repositories/eventRepository"

export async function getEvents() {
    try {
        return await fetchEvents()
    } catch (error) {
        console.error(error)
        return []
    }
}

export async function createEvent(eventData) {
    try {
        return await createEventRepository(eventData)
    } catch (error) {
        console.error(error)
        return null
    }
}

export async function getUserEvents(ownerId) {
    try {
        return await fetchUserEventsRepository(ownerId)
    } catch (error) {
        console.error(error)
        return []
    }
}

export async function getEvent(eventId) {
    try {
        return await fetchEventRepository(eventId)
    } catch (error) {
        console.error(error)
        return null
    }
}

export async function deleteEvent(eventId) {
    try {
        return await deleteEventRepository(eventId)
    } catch (error) {
        console.error(error)
    }
}

export async function editEvent(eventId, eventData) {
    try {
        return await updateEventRepository(eventId, eventData)
    } catch (error) {
        console.error(error)
        return null
    }
}
