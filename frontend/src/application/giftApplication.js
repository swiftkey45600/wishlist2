import {
  fetchGift,
  fetchGiftsByEvent,
  createGift as createGiftRepository,
  updateGiftStatus as updateGiftStatusRepository,
  deleteGift as deleteGiftRepository,
  reserveGift as reserveGiftRepository,
  unreserveGift as unreserveGiftRepository,
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

export async function updateGiftStatus(giftId, status) {
  try {
    return await updateGiftStatusRepository(giftId, status)
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

export async function reserveGift(giftId, reserverName, isAnonymous = false) {
  try {
    return await reserveGiftRepository(giftId, reserverName, isAnonymous)
  } catch (error) {
    console.error(error)
    return null
  }
}

export async function unreserveGift(reservationId) {
  try {
    return await unreserveGiftRepository(reservationId)
  } catch (error) {
    console.error(error)
    return null
  }
}