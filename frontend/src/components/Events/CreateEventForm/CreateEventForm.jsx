import "./CreateEventForm.css"
import { useState } from "react"

function CreateEventForm({ onCreateEvent }) {
    const [title, setTitle] = useState("")
    const [description, setDescription] = useState("")
    const [place, setPlace] = useState("")
    const [eventDate, setEventDate] = useState("")

    function handleSubmit(event) {
        event.preventDefault()
        onCreateEvent(title, description, place, eventDate)
    }

    return (
        <form className="create-event-form" onSubmit={handleSubmit}>
            <h2>Создать новое событие</h2>

            <div className="create-event-form-fields">
                <div className="create-event-form-header">
                    <input
                        placeholder="Название события"
                        value={title}
                        onChange={(event) => setTitle(event.target.value)}
                    />

                    <input
                        placeholder="Описание события"
                        value={description}
                        onChange={(event) => setDescription(event.target.value)}
                    />
                </div>

                <div className="create-event-form-footer">
                    <input
                        placeholder="Место"
                        value={place}
                        onChange={(event) => setPlace(event.target.value)}
                    />

                    <input
                        type="datetime-local"
                        placeholder="Время"
                        value={eventDate}
                        onChange={(event) => setEventDate(event.target.value)}
                    />

                    <button type="submit">Создать событие</button>
                </div>
            </div>
        </form>
    )
}

export default CreateEventForm
