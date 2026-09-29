import {
    fetchEventTags,
    createEventTag,
    updateEventTag,
    deleteEventTag
} from "../repositories/tagRepository"
import { mockTags } from "../mocks/mockTags"

const USE_TAG_MOCKS = true

export async function getEventTags(eventId) {
    if (USE_TAG_MOCKS) {
        return mockTags.map(tag => ({
            ...tag,
            event_id: Number(eventId)
        }))
    }

    try {
        return await fetchEventTags(eventId)
    } catch (error) {
        console.error(error)
        return mockTags.map(tag => ({
            ...tag,
            event_id: Number(eventId)
        }))
    }
}

export async function createTag(eventId, name) {
    if (USE_TAG_MOCKS) {
        return {
            id: Date.now(),
            event_id: Number(eventId),
            name
        }
    }

    try {
        return await createEventTag(eventId, name)
    } catch (error) {
        console.error(error)
        return {
            id: Date.now(),
            event_id: Number(eventId),
            name
        }
    }
}

export async function editTag(tagId, name) {
    if (USE_TAG_MOCKS) {
        return { id: Number(tagId), name }
    }

    try {
        return await updateEventTag(tagId, name)
    } catch (error) {
        console.error(error)
        return null
    }
}

export async function deleteTag(tagId) {
    if (USE_TAG_MOCKS) {
        return Boolean(tagId)
    }

    try {
        await deleteEventTag(tagId)
        return true
    } catch (error) {
        console.error(error)
        return false
    }
}
