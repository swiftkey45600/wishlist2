const PRIORITY_STORAGE_PREFIX = "wishlist.gift-priority."
const validPriorities = new Set(["high", "normal", "low"])

export function saveGiftPriority(giftId, priority) {
    if (giftId == null || !validPriorities.has(priority)) return

    try {
        localStorage.setItem(`${PRIORITY_STORAGE_PREFIX}${giftId}`, priority)
    } catch (error) {
        console.error("Не удалось сохранить приоритет подарка локально", error)
    }
}

export function applySavedGiftPriorities(gifts) {
    return gifts.map(gift => {
        const apiPriority = validPriorities.has(gift.priority) ? gift.priority : "normal"
        try {
            const key = `${PRIORITY_STORAGE_PREFIX}${gift.id}`
            const savedPriority = localStorage.getItem(key)
            const priority = validPriorities.has(gift.priority)
                ? apiPriority
                : validPriorities.has(savedPriority) ? savedPriority : apiPriority
            localStorage.setItem(key, priority)
            return { ...gift, priority }
        } catch (error) {
            console.error("Не удалось загрузить локальный приоритет подарка", error)
            return { ...gift, priority: apiPriority }
        }
    })
}

export function removeSavedGiftPriority(giftId) {
    if (giftId == null) return

    try {
        localStorage.removeItem(`${PRIORITY_STORAGE_PREFIX}${giftId}`)
    } catch (error) {
        console.error("Не удалось удалить локальный приоритет подарка", error)
    }
}
