import { useEffect, useState } from "react"
import "./EventsList.css"

import EventCard from "../EventCard/EventCard"
import { getGiftsByEvent } from "../../../application/giftApplication"

function EventsList({ events, onOpenEvent, onGiftsLoaded }) {
    const [giftsByEvent, setGiftsByEvent] = useState({})

    useEffect(() => {
        let isCurrent = true

        async function loadGifts() {
            const giftEntries = await Promise.all(events.map(async (event) => {
                const gifts = await getGiftsByEvent(event.id)
                return [event.id, Array.isArray(gifts) ? gifts : []]
            }))

            if (isCurrent) {
                const loadedGiftsByEvent = Object.fromEntries(giftEntries)
                setGiftsByEvent(loadedGiftsByEvent)
                onGiftsLoaded?.(loadedGiftsByEvent)
            }
        }

        loadGifts()
        return () => { isCurrent = false }
    }, [events, onGiftsLoaded])

    return (
        <div className="events-list">
            <h2>События</h2>
            {events.map((event) => <EventCard key={event.id} event={event} gifts={giftsByEvent[event.id] || []} onOpenEvent={onOpenEvent} />)}
        </div>
    )
}

export default EventsList
