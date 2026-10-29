import { useEffect, useState } from "react"
import "./EventsList.css"

import EventCard from "../EventCard/EventCard"
import { getGiftsByEvent } from "../../../application/giftApplication"
import { applySavedGiftPriorities } from "../../../application/giftPriorityApplication"

function EventsList({ events, onOpenEvent, onGiftsLoaded }) {
    const [giftsByEvent, setGiftsByEvent] = useState({})
    const [error, setError] = useState("")

    useEffect(() => {
        let isCurrent = true

        async function loadGifts() {
            try {
                const giftEntries = await Promise.all(events.map(async (event) => {
                    const gifts = await getGiftsByEvent(event.id)
                    return [event.id, Array.isArray(gifts) ? applySavedGiftPriorities(gifts.filter(gift => !gift.received && !gift.carried_forward)) : []]
                }))

                if (isCurrent) {
                    setError("")
                    const loadedGiftsByEvent = Object.fromEntries(giftEntries)
                    setGiftsByEvent(loadedGiftsByEvent)
                    onGiftsLoaded?.(loadedGiftsByEvent)
                }
            } catch {
                if (isCurrent) setError("Не удалось загрузить подарки событий. Обновите страницу.")
            }
        }

        loadGifts()
        return () => { isCurrent = false }
    }, [events, onGiftsLoaded])

    return (
        <div className="events-list">
            <h2>События</h2>
            {error && <p role="alert">{error}</p>}
            {!error && events.map((event) => <EventCard key={event.id} event={event} gifts={giftsByEvent[event.id] || []} onOpenEvent={onOpenEvent} />)}
        </div>
    )
}

export default EventsList
