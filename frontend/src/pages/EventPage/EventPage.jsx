import { useEffect, useState } from "react"
import "./EventPage.css"
import "../../Styles/common.css"

import { useNavigate, useParams } from "react-router-dom"
import { getEvent } from "../../application/eventApplication"

import Sidebar from "../../components/Sidebar/Sidebar"
import EventDetailsCard from "../../components/Events/EventDetailsCard/EventDetailsCard"
import GiftList from "../../components/Gifts/GiftList/GiftList"

function EventPage() {
	const navigate = useNavigate()
    const { id } = useParams()
    const [event, setEvent] = useState(null)
    const [isLoading, setIsLoading] = useState(true)
    const [showToast, setShowToast] = useState(false)

    useEffect(() => {
        async function loadEvent() {
            setIsLoading(true)

            const eventById = await getEvent(id)
            setEvent(eventById)

            setIsLoading(false)
        }

        loadEvent()
    }, [id])

    useEffect(() => {
        if (!showToast) return

        const timer = window.setTimeout(() => setShowToast(false), 2000)

        return () => window.clearTimeout(timer)
    }, [showToast])

    async function handleShare() {
        const shareLink = event?.public_token
            ? `${window.location.origin}/share/${event.public_token}`
            : window.location.href

        try {
            if (navigator.clipboard?.writeText) {
                await navigator.clipboard.writeText(shareLink)
            } else {
                const textArea = document.createElement("textarea")
                textArea.value = shareLink
                textArea.setAttribute("readonly", "")
                textArea.style.position = "fixed"
                textArea.style.top = "-9999px"
                document.body.appendChild(textArea)
                textArea.select()
                document.execCommand("copy")
                document.body.removeChild(textArea)
            }

            setShowToast(true)
        } catch (error) {
            console.error("Не удалось скопировать ссылку", error)
        }
    }

	return (
		<div className="page-layout">
				<Sidebar />

				<div className="page-content">
					<div className="event-page-actions">
						<button className="back-button" onClick={() => navigate("/")}>
							← Назад к событиям
						</button>
						<button className="share-button" onClick={handleShare}>
							Поделиться
						</button>
					</div>

					{showToast && <div className="share-toast">Ссылка скопирована</div>}

                    {
                        isLoading && (
                            <p className="event-page-status">
                                Загружаем информацию о событии...
                            </p>
                        )
                    }

                    {
                        !isLoading && !event && (
                            <p className="event-page-status">
                                Событие с id {id} не найдено
                            </p>
                        )
                    }

                    {
                        !isLoading && event && (
                            <>
                                <EventDetailsCard event={event} />
                                <GiftList eventId={id} />
                            </>
                        )
                    }
				</div>
		</div>
	)
}

export default EventPage
