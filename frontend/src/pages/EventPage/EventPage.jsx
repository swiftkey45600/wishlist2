import { useEffect, useState } from "react"
import "./EventPage.css"
import "../../Styles/common.css"

import { useNavigate, useParams } from "react-router-dom"
import { deleteEvent, editEvent, getEvent } from "../../application/eventApplication"

import Header from "../../components/Header/Header"
import Sidebar from "../../components/Sidebar/Sidebar"
import EventDetailsCard from "../../components/Events/EventDetailsCard/EventDetailsCard"
import GiftList from "../../components/Gifts/GiftList/GiftList"
import ConfirmDeleteModal from "../../components/ConfirmDeleteModal/ConfirmDeleteModal"
import EditEventForm from "../../components/Events/EditEventForm/EditEventForm"

function EventPage() {
	const navigate = useNavigate()
    const { id } = useParams()
    const [event, setEvent] = useState(null)
    const [isLoading, setIsLoading] = useState(true)
    const [showToast, setShowToast] = useState(false)
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
    const [isEditModalOpen, setIsEditModalOpen] = useState(false)
    const user = JSON.parse(localStorage.getItem("user") || "null")
    const isOwner = user?.id === event?.owner_id

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

    async function handleDeleteEvent() {
        await deleteEvent(id)
        navigate("/")
    }

    async function handleEditEvent(eventData) {
        const updatedEvent = await editEvent(id, eventData)
        if (!updatedEvent) return false

        setEvent(updatedEvent)
        setIsEditModalOpen(false)
        return true
    }

    return (
        <div className="event-shell">
            <Header />
            <div className="page-layout event-layout">
                <Sidebar activeSection="events" />

                <main className="page-content event-content">
                    <button className="event-back" onClick={() => navigate("/")}>
                        ← Все события
                    </button>

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
                                <EventDetailsCard
                                    event={event}
                                    onShare={isOwner ? handleShare : undefined}
                                    onEdit={isOwner ? () => setIsEditModalOpen(true) : undefined}
                                    onDelete={isOwner ? () => setIsDeleteModalOpen(true) : undefined}
                                />
                                <GiftList eventId={id} isOwner={isOwner} />
                                {isEditModalOpen && (
                                    <div className="event-edit-modal" onClick={(modalEvent) => {
                                        if (modalEvent.target === modalEvent.currentTarget) setIsEditModalOpen(false)
                                    }}>
                                        <div className="event-edit-dialog">
                                            <EditEventForm
                                                event={event}
                                                onSave={handleEditEvent}
                                                onCancel={() => setIsEditModalOpen(false)}
                                            />
                                        </div>
                                    </div>
                                )}
                                {isDeleteModalOpen && (
                                    <ConfirmDeleteModal
                                        itemName="событие"
                                        onConfirm={handleDeleteEvent}
                                        onCancel={() => setIsDeleteModalOpen(false)}
                                    />
                                )}
                            </>
                        )
                    }
                </main>
		</div>
        </div>
	)
}

export default EventPage
