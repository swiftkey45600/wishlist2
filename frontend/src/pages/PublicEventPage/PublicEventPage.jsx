import { useEffect, useState } from "react"
import "../EventPage/EventPage.css"
import "../../styles/common.css"

import { useNavigate, useParams } from "react-router-dom"

import api from "../../services/api"
import Sidebar from "../../components/Sidebar/Sidebar"
import EventDetailsCard from "../../components/Events/EventDetailsCard/EventDetailsCard"
import GiftCard from "../../components/Gifts/GiftCard/GiftCard"
import { editGift } from "../../application/giftApplication"
import GuestReservationModal from "../../components/Gifts/GuestReservationModal/GuestReservationModal"
import {
    getGuestReservationGifts,
    useGuestReservationMocks
} from "../../application/guestReservationApplication"

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

    async function handleToggleStatus(gift) {
        if (gift.status === "bought") return
        if (!isAuthenticated) {
            setReservationError(null)
            setSelectedGift({ gift, token })
            return
        }

        setReservationError(null)
        const updatedGift = await editGift(gift.id, {
            is_reserved: gift.status === "available"
        })

        if (!updatedGift) {
            setReservationError("Не удалось изменить бронь. Возможно, подарок уже заняли.")
            return
        }

        setData(previous => ({
            ...previous,
            gifts: previous.gifts.map(item => item.id === gift.id ? updatedGift : item)
        }))
    }

    useEffect(() => {
        let cancelled = false
        async function loadPublicEvent() {
            setIsLoading(true)

            try {
                const response = await api.get(`/events/public/${token}`)
                const gifts = await getGuestReservationGifts(token, response.data.gifts || [])
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

    return (
        <div className="page-layout">
            <Sidebar />

            <div className="page-content">
                <div className="event-page-actions">
                    <button className="back-button" onClick={() => navigate("/")}>
                        ← Назад к событиям
                    </button>
                    <span className="event-page-note">
                        {isOwner
                            ? "Это ваше событие"
                            : isAuthenticated
                                ? "Вы можете забронировать подарок"
                                : "Откройте подарок, чтобы выбрать способ бронирования"}
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
                        {useGuestReservationMocks && <p className="guest-reservation-demo" role="status">
                            Демо гостевой брони: изменения видны только здесь и сбросятся после обновления страницы.
                        </p>}

                        <div className="gift-list">
                            <div className="gift-list-header">
                                <h2>Подарки • {data.gifts?.length ?? 0}</h2>
                            </div>

                            {!data.gifts?.length && (
                                <p className="gift-list-status">Пока нет подарков для этого события.</p>
                            )}

                            {reservationError && (
                                <p className="gift-list-status error">{reservationError}</p>
                            )}

                            {data.gifts?.length > 0 && (
                                <div className="gift-grid">
                                    {data.gifts.map((gift) => (
                                        <GiftCard
                                            key={gift.id}
                                            gift={gift}
                                            onToggleStatus={!isOwner && gift.status !== "bought" ? handleToggleStatus : undefined}
                                        />
                                    ))}
                                </div>
                            )}
                        </div>
                    </>
                )}
            </div>
            {selectedGift?.token === token && !isLoading && <GuestReservationModal
                key={`${token}:${selectedGift.gift.id}`}
                token={token}
                gift={selectedGift.gift}
                onCancel={() => setSelectedGift(null)}
                onSuccess={updatedGift => {
                    setData(previous => ({
                        ...previous,
                        gifts: previous.gifts.map(gift => gift.id === updatedGift.id ? updatedGift : gift)
                    }))
                    setSelectedGift(null)
                }}
            />}
        </div>
    )
}

export default PublicEventPage
