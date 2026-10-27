import { useEffect, useState } from "react"
import "../EventPage/EventPage.css"
import "../../styles/common.css"

import { useNavigate, useParams } from "react-router-dom"

import api from "../../services/api"
import Header from "../../components/Header/Header"
import Sidebar from "../../components/Sidebar/Sidebar"
import EventDetailsCard from "../../components/Events/EventDetailsCard/EventDetailsCard"
import GiftCard from "../../components/Gifts/GiftCard/GiftCard"
import { updatePublicGiftReservation } from "../../application/giftApplication"
import GuestReservationModal from "../../components/Gifts/GuestReservationModal/GuestReservationModal"
import GiftFilters from "../../components/Gifts/GiftFilters/GiftFilters"
import { useGiftFilters } from "../../components/Gifts/GiftFilters/useGiftFilters"
import { applySavedGiftPriorities } from "../../application/giftPriorityApplication"

function PublicEventPage() {
    const navigate = useNavigate()
    const { token } = useParams()
    const [data, setData] = useState(null)
    const [isLoading, setIsLoading] = useState(true)
    const [reservationError, setReservationError] = useState(null)
    const [selectedGift, setSelectedGift] = useState(null)

    const user = JSON.parse(localStorage.getItem("user") || "null")
    const isAuthenticated = Boolean(localStorage.getItem("accessToken"))
    const isOwner = isAuthenticated && user?.id === data?.event?.owner_id
    const gifts = data?.gifts || []
    const tags = []
    gifts.forEach((gift) => {
        gift.tags?.forEach((tag) => {
            if (!tags.some((existingTag) => existingTag.id === tag.id)) tags.push(tag)
        })
    })
    const { filters, filteredGifts, updateFilter } = useGiftFilters(gifts, isOwner)

    async function handleToggleStatus(gift) {
        if (gift.status === "bought") return
        if (!isAuthenticated) {
            setReservationError(null)
            setSelectedGift({ gift, token })
            return
        }

        setReservationError(null)
        const updatedGift = await updatePublicGiftReservation(token, gift.id, gift.status === "available")

        if (!updatedGift) {
            setReservationError("Не удалось изменить бронь. Возможно, подарок уже заняли.")
            return
        }

        setData(previous => previous?.event?.public_token === token ? ({
            ...previous,
            gifts: previous.gifts.map(item => item.id === gift.id
                ? applySavedGiftPriorities([{ ...updatedGift, priority: updatedGift.priority || item.priority }])[0]
                : item)
        }) : previous)
    }

    async function handleFundraisingChange() {
        const response = await api.get(`/events/public/${token}`)
        const gifts = applySavedGiftPriorities(response.data.gifts || [])
        setData(previous => previous?.event?.public_token === token ? { ...response.data, gifts } : previous)
    }

    useEffect(() => {
        let cancelled = false
        async function loadPublicEvent() {
            setIsLoading(true)

            try {
                const response = await api.get(`/events/public/${token}`)
                const gifts = applySavedGiftPriorities(response.data.gifts || [])
                if (!cancelled) setData({ ...response.data, gifts })
            } catch (error) {
                console.error("Не удалось загрузить публичное событие", error)
                if (!cancelled) setData(null)
            } finally {
                if (!cancelled) setIsLoading(false)
            }
        }

        loadPublicEvent()
        return () => { cancelled = true }
    }, [token])

    useEffect(() => {
        const title = data?.event?.title
        if (!title) return

        const previousTitle = document.title
        document.title = `${title} — Wishlist`
        return () => { document.title = previousTitle }
    }, [data?.event?.title])

    return (
        <div className="event-shell">
            <Header />
            <div className="page-layout event-layout">
                <Sidebar activeSection="events" />

                <main className="page-content event-content public-event-content">
                    <div className="public-event-actions">
                        <button className="event-back" onClick={() => navigate(-1)}>
                            ← Назад
                        </button>
                        <span className="event-page-note">
                            {isOwner
                                ? "Это ваше событие"
                                : isAuthenticated
                                    ? "Вы можете забронировать подарок"
                                    : "Вы можете забронировать подарок без регистрации"}
                        </span>
                    </div>

                    {isLoading && (
                        <p className="event-page-status">Загружаем информацию о событии...</p>
                    )}

                    {!isLoading && !data && (
                        <p className="event-page-status">Событие не найдено или ссылка недействительна.</p>
                    )}

                    {!isLoading && data && (
                        <>
                            <EventDetailsCard event={data.event} />

                            <div className="gift-list">
                                <div className="public-gift-list-header">
                                    <h2>Подарки</h2>
                                    <span>{filteredGifts.length} из {gifts.length}</span>
                                </div>

                                <GiftFilters
                                    hideStatus={isOwner}
                                    tags={tags}
                                    filters={filters}
                                    onFilterChange={updateFilter}
                                />

                                {!gifts.length && (
                                    <p className="gift-list-status">Пока нет подарков для этого события.</p>
                                )}

                                {gifts.length > 0 && filteredGifts.length === 0 && (
                                    <p className="gift-list-status">Подарки по заданным фильтрам не найдены.</p>
                                )}

                                {reservationError && (
                                    <p className="gift-list-status error">{reservationError}</p>
                                )}

                                {filteredGifts.length > 0 && (
                                    <div className="gift-grid">
                                        {filteredGifts.map((gift) => (
                                            <GiftCard
                                                key={`${token}:${gift.id}`}
                                                gift={gift}
                                                publicToken={token}
                                                isOwner={isOwner}
                                                onGiftChange={handleFundraisingChange}
                                                hideReservationDetails={isOwner}
                                                onToggleStatus={!isOwner && gift.status !== "bought" ? handleToggleStatus : undefined}
                                            />
                                        ))}
                                    </div>
                                )}
                            </div>
                        </>
                    )}
                </main>
            </div>
            {selectedGift?.token === token && !isLoading && <GuestReservationModal
                key={`${token}:${selectedGift.gift.id}`}
                token={token}
                gift={selectedGift.gift}
                onCancel={() => setSelectedGift(null)}
                onSuccess={updatedGift => {
                    setData(previous => previous?.event?.public_token === token ? ({
                        ...previous,
                        gifts: previous.gifts.map(gift => gift.id === updatedGift.id
                            ? applySavedGiftPriorities([{
                                ...updatedGift,
                                priority: updatedGift.priority || gift.priority
                            }])[0]
                            : gift)
                    }) : previous)
                    setSelectedGift(null)
                }}
            />}
        </div>
    )
}

export default PublicEventPage
