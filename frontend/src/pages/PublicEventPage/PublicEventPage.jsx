import { useEffect, useState } from "react"
import "../EventPage/EventPage.css"
import "../../Styles/common.css"

import { useNavigate, useParams } from "react-router-dom"

import api from "../../services/api"
import Sidebar from "../../components/Sidebar/Sidebar"
import EventDetailsCard from "../../components/Events/EventDetailsCard/EventDetailsCard"
import GiftCard from "../../components/Gifts/GiftCard/GiftCard"

function PublicEventPage() {
    const navigate = useNavigate()
    const { token } = useParams()
    const [data, setData] = useState(null)
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        async function loadPublicEvent() {
            setIsLoading(true)

            try {
                const response = await api.get(`/events/public/${token}`)
                setData(response.data)
            } catch (error) {
                console.error("Не удалось загрузить публичное событие", error)
                setData(null)
            } finally {
                setIsLoading(false)
            }
        }

        loadPublicEvent()
    }, [token])

    return (
        <div className="page-layout">
            <Sidebar />

            <div className="page-content">
                <div className="event-page-actions">
                    <button className="back-button" onClick={() => navigate("/")}>
                        ← Назад к событиям
                    </button>
                    <span className="event-page-note">Просмотр только для чтения</span>
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
                            <div className="gift-list-header">
                                <h2>Подарки • {data.gifts?.length ?? 0}</h2>
                            </div>

                            {!data.gifts?.length && (
                                <p className="gift-list-status">Пока нет подарков для этого события.</p>
                            )}

                            {data.gifts?.length > 0 && (
                                <div className="gift-grid">
                                    {data.gifts.map((gift) => (
                                        <GiftCard key={gift.id} gift={gift} />
                                    ))}
                                </div>
                            )}
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}

export default PublicEventPage
