import {
    fetchEvents,
    createEvent as createEventRepository,
    fetchUserEvents as fetchUserEventsRepository,
    fetchEvent as fetchEventRepository,
    fetchEventStatistics as fetchEventStatisticsRepository,
    deleteEvent as deleteEventRepository,
    updateEvent as updateEventRepository
} from "../repositories/eventRepository"

export async function getEvents(status) {
    return fetchEvents(status)
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

export async function getEventStatistics(eventId) {
    try {
        return await fetchEventStatisticsRepository(eventId)
    } catch (error) {
        console.error(error)
        return null
    }
}

export async function deleteEvent(eventId, keepGifts = false) {
    try {
        await deleteEventRepository(eventId, keepGifts)
        return true
    } catch (error) {
        console.error(error)
        return false
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
