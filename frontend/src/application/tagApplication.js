import { fetchEventTags, createEventTag, updateEventTag, deleteEventTag } from "../repositories/tagRepository"

export async function getEventTags(eventId) {
    return await fetchEventTags(eventId)
}

export async function createTag(eventId, name) {
    return await createEventTag(eventId, name)
}

export async function editTag(tagId, name) {
    return await updateEventTag(tagId, name)
}

export async function deleteTag(tagId) {
    await deleteEventTag(tagId)
    return true
}
