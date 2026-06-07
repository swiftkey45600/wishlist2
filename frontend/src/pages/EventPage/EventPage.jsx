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

    useEffect(() => {
        async function loadEvent() {
            setIsLoading(true)

            const eventById = await getEvent(id)
            setEvent(eventById)

            setIsLoading(false)
        }

        loadEvent()
    }, [id])

	return (
		<div className="page-layout">
				<Sidebar />

				<div className="page-content">
					<button className="back-button" onClick={() => navigate("/")}>
						← Назад к событиям
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
