import "./CreateEventForm.css"
import { useState } from "react"

function CreateEventForm({ onCreateEvent }) {
    const [title, setTitle] = useState("")
    const [description, setDescription] = useState("")
    const [place, setPlace] = useState("")
    const [eventDate, setEventDate] = useState("")

    return (
        <div className="create-event-form">
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
                        onChange={
                            (event) => {console.log(event.target.value); 
                            setEventDate(event.target.value)}}
                    />

                    <button onClick={() => onCreateEvent(title, description, place, eventDate)}>Создать событие</button>
                </div>
            </div>
        </div>
    )
}

export default CreateEventForm
