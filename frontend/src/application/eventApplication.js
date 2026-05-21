import {
    fetchEvents,
    createEvent as createEventRepositury,
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
        return await createEventRepositury(eventData)
    } catch (error) {
        console.error(error)
        return {
            id: Date.now(),
            ...eventData,
            event_date: eventData.date
        }
    }
}

export async function deleteEvent(eventId) {
    try {
        return await deleteEventRepository(eventId)
    } catch (error) {
        console.error(error)
    }
}
