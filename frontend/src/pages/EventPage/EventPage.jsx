import { useEffect, useState } from "react"
import "./EventPage.css"
import "../../styles/common.css"

import { useNavigate, useParams } from "react-router-dom"
import { deleteEvent, editEvent, getEvent } from "../../application/eventApplication"

import Header from "../../components/Header/Header"
import Sidebar from "../../components/Sidebar/Sidebar"
import EventDetailsCard from "../../components/Events/EventDetailsCard/EventDetailsCard"
import GiftList from "../../components/Gifts/GiftList/GiftList"
import ConfirmDeleteModal from "../../components/ConfirmDeleteModal/ConfirmDeleteModal"
import EditEventForm from "../../components/Events/EditEventForm/EditEventForm"
import GiftPriceWidget from "../../components/Gifts/GiftPriceWidget/GiftPriceWidget"
import ShareEventModal from "../../components/Events/ShareEventModal/ShareEventModal"

function EventPage() {
	const navigate = useNavigate()
    const { id } = useParams()
    const [event, setEvent] = useState(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
    const [isEditModalOpen, setIsEditModalOpen] = useState(false)
    const [isShareModalOpen, setIsShareModalOpen] = useState(false)
    const [statisticsRefreshKey, setStatisticsRefreshKey] = useState(0)
    const user = JSON.parse(localStorage.getItem("user") || "null")
    const isOwner = user?.id === event?.owner_id
    const shareLink = event?.public_token
        ? `${window.location.origin}/share/${event.public_token}`
        : window.location.href

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
        if (!event?.title) return
        const previousTitle = document.title
        document.title = `${event.title} — Wishlist`
        return () => { document.title = previousTitle }
    }, [event?.title])

    async function handleDeleteEvent() {
        if (!await deleteEvent(id)) return false
        navigate("/")
        return true
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
                                    onShare={isOwner ? () => setIsShareModalOpen(true) : undefined}
                                    onEdit={isOwner ? () => setIsEditModalOpen(true) : undefined}
                                    onDelete={isOwner ? () => setIsDeleteModalOpen(true) : undefined}
                                />
                                {isOwner && (
                                    <GiftPriceWidget eventId={id} refreshKey={statisticsRefreshKey} />
                                )}
                                <GiftList
                                    key={id}
                                    eventId={id}
                                    isOwner={isOwner}
                                    onGiftDataChange={() => setStatisticsRefreshKey((key) => key + 1)}
                                />
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
                                {isShareModalOpen && shareLink && (
                                    <ShareEventModal
                                        event={event}
                                        shareLink={shareLink}
                                        onClose={() => setIsShareModalOpen(false)}
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
