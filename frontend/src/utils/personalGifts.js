// Event imports remain separate for reservations, but represent one wish here.
export function uniquePersonalGifts(gifts) {
    const key = gift => `${gift.isPersonal ? "wish" : "gift"}:${gift.id}`
    const byKey = new Map(gifts.map(gift => [key(gift), gift]))
    function identity(gift, visited = new Set()) {
        const ownKey = key(gift)
        if (visited.has(ownKey)) return ownKey
        visited.add(ownKey)
        const sourceKey = gift.source_wish_id != null ? `wish:${gift.source_wish_id}`
            : gift.source_gift_id != null ? `gift:${gift.source_gift_id}` : null
        return sourceKey ? (byKey.has(sourceKey) ? identity(byKey.get(sourceKey), visited) : sourceKey) : ownKey
    }
    const result = new Map()
    for (const gift of gifts) {
        if (gift.carried_forward) continue
        const id = identity(gift)
        const current = result.get(id)
        // A received event gift takes precedence over its unreceived source.
        if (!current || (gift.received && !current.received)) result.set(id, gift)
    }
    return [...result.values()]
}
