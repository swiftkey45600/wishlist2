import {
  fetchGift,
  fetchGiftsByEvent,
  createGift as createGiftRepository,
  deleteGift as deleteGiftRepository,
  updateGift as updateGiftRepository
} from "../repositories/giftRepository"

export async function getGift(giftId) {
  try {
    return await fetchGift(giftId)
  } catch (error) {
    console.error(error)
    return []
  }
}

export async function getGiftsByEvent(eventId) {
  try {
    return await fetchGiftsByEvent(eventId)
  } catch (error) {
    console.error(error)
    return []
  }
}

export async function createGift(giftData) {
  try {
    return await createGiftRepository(giftData)
  } catch (error) {
    console.error(error)
    return null
  }
}

export async function editGift(giftId, data) {
  try {
    return await updateGiftRepository(giftId, data)
  } catch (error) {
    console.error(error)
    return null
  }
}

export async function deleteGift(giftId) {
  try {
    return await deleteGiftRepository(giftId)
  } catch (error) {
    console.error(error)
  }
}
