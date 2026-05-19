import "./EventPage.css"

import { useNavigate } from "react-router-dom"

import Sidebar from "../../components/Sidebar/Sidebar"
import EventDetailsCard from "../../components/Events/EventDetailsCard/EventDetailsCard"
import GiftList from "../../components/Gifts/GiftList/GiftList"

function EventPage() {
	const navigate = useNavigate()

	return (
		<div className="event-page-layout">
				<Sidebar />

				<div className="event-page-content">
					<button className="back-button" onClick={() => navigate("/")}>
						← Назад к событиям
					</button>

					<EventDetailsCard />

					<GiftList />
				</div>
		</div>
	)
}

export default EventPage
