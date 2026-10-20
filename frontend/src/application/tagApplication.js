import {
    fetchEventTags,
    createEventTag,
    updateEventTag,
    deleteEventTag
} from "../repositories/tagRepository"

export async function getEventTags(eventId) {
    return fetchEventTags(eventId)
}

export async function createTag(eventId, name) {
    return createEventTag(eventId, name)
}

export async function editTag(eventId, tagId, name) {
    return updateEventTag(eventId, tagId, name)
}

export async function deleteTag(eventId, tagId) {
    await deleteEventTag(eventId, tagId)
    return true
}
