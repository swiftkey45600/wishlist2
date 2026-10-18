import {
  fetchGift,
  fetchGiftsByEvent,
  createGift as createGiftRepository,
  deleteGift as deleteGiftRepository,
  updateGift as updateGiftRepository,
  updatePublicGiftReservation as updatePublicGiftReservationRepository,
  reserveGift as reserveGiftRepository,
  unreserveGift as unreserveGiftRepository
} from "../repositories/giftRepository"

export async function getGift(giftId) {
  try {
    return await fetchGift(giftId)
  } catch (error) {
    console.error(error)
    return []
  }
}

export async function getGiftsByEvent(eventId, showReservations = false) {
  try {
    return await fetchGiftsByEvent(eventId, showReservations)
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

export async function reserveGift(giftId, isAnonymous = false) {
  try {
    return await reserveGiftRepository(giftId, isAnonymous)
  } catch (error) {
    console.error(error)
    return null
  }
}

export async function updatePublicGiftReservation(token, giftId, isReserved) {
  try {
    return await updatePublicGiftReservationRepository(token, giftId, isReserved)
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

export async function deleteGift(giftId) {
  try {
    await deleteGiftRepository(giftId)
    return true
  } catch (error) {
    console.error(error)
    return false
  }
}
