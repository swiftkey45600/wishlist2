import "./CreateEventForm.css"
import { useState } from "react"

function CreateEventForm({ onCreateEvent, onCancel }) {
    const [title, setTitle] = useState("")
    const [description, setDescription] = useState("")
    const [place, setPlace] = useState("")
    const [eventDate, setEventDate] = useState("")
    const [error, setError] = useState("")

    function handleSubmit(event) {
        event.preventDefault()
        const trimmedTitle = title.trim()

        if (!trimmedTitle) {
            setError("Введите название события")
            return
        }

        setError("")
        onCreateEvent(trimmedTitle, description.trim(), place.trim(), eventDate)
    }

    return (
        <div className="create-event-form">
            <h2>Создать событие</h2>
            <form className="create-event-form-fields" onSubmit={handleSubmit}>
                <label className="create-event-field">Название<input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Например, День рождения" autoFocus /></label>
                <label className="create-event-field">Описание<input value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Описание события" /></label>
                <label className="create-event-field">Дата и время<input value={eventDate} type="datetime-local" onChange={(event) => setEventDate(event.target.value)} /></label>
                <label className="create-event-field">Место<input value={place} onChange={(event) => setPlace(event.target.value)} placeholder="Город или место" /></label>
                {error && <p className="create-event-error">{error}</p>}
                <div className="create-event-actions">
                    <button type="button" className="create-event-secondary" onClick={onCancel}>Отмена</button>
                    <button type="submit" className="create-event-primary">Создать</button>
                </div>
            </form>
        </div>
    )
}

export default CreateEventForm
