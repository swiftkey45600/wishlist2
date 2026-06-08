import {
    fetchEvents,
    createEvent as createEventRepository,
    fetchUserEvents as fetchUserEventsRepository,
    fetchEvent as fetchEventRepository,
    deleteEvent as deleteEventRepository
} from "../repositories/eventRepository"

import { mockEvents } from "../mocks/mockEvents"

export async function getEvents() {
    try {
        return await fetchEvents()
    } catch (error) {
        console.error(error)
        return mockEvents
    }
}

export async function createEvent(eventData) {
    try {
        return await createEventRepository(eventData)
    } catch (error) {
        console.error(error)
        return {
            id: Date.now(),
            ...eventData,
            event_date: eventData.event_date
        }
    }
}

export async function getUserEvents(ownerId) {
    try {
        return await fetchUserEventsRepository(ownerId)
    } catch (error) {
        console.error(error)
        return mockEvents
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
