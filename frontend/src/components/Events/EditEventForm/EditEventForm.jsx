import { useState } from "react"
import "../CreateEventForm/CreateEventForm.css"

function getDateTimeValue(value) {
    if (!value) return ""

    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return ""

    const offset = date.getTimezoneOffset() * 60000
    return new Date(date.getTime() - offset).toISOString().slice(0, 16)
}

function EditEventForm({ event, onSave, onCancel }) {
    const [title, setTitle] = useState(event.title || "")
    const [description, setDescription] = useState(event.description || "")
    const [place, setPlace] = useState(event.place || "")
    const [eventDate, setEventDate] = useState(getDateTimeValue(event.event_date))
    const [error, setError] = useState("")
    const [isSaving, setIsSaving] = useState(false)

    async function handleSubmit(submitEvent) {
        submitEvent.preventDefault()

        if (!title.trim()) {
            setError("Введите название события")
            return
        }

        setError("")
        setIsSaving(true)
        const saved = await onSave({
            title: title.trim(),
            description: description.trim(),
            place: place.trim(),
            event_date: eventDate || null
        })
        setIsSaving(false)

        if (!saved) setError("Не удалось сохранить изменения")
    }

    return (
        <div className="create-event-form">
            <h2>Редактировать событие</h2>
            <form className="create-event-form-fields" onSubmit={handleSubmit}>
                <label className="create-event-field">
                    Название
                    <input value={title} onChange={(inputEvent) => setTitle(inputEvent.target.value)} autoFocus />
                </label>
                <label className="create-event-field">
                    Описание
                    <textarea value={description} onChange={(inputEvent) => setDescription(inputEvent.target.value)} />
                </label>
                <label className="create-event-field">
                    Дата и время
                    <input value={eventDate} type="datetime-local" onChange={(inputEvent) => setEventDate(inputEvent.target.value)} />
                </label>
                <label className="create-event-field">
                    Место
                    <input value={place} onChange={(inputEvent) => setPlace(inputEvent.target.value)} />
                </label>
                {error && <p className="create-event-error">{error}</p>}
                <div className="create-event-actions">
                    <button type="button" className="create-event-secondary" onClick={onCancel}>Отмена</button>
                    <button type="submit" className="create-event-primary" disabled={isSaving}>
                        {isSaving ? "Сохранение..." : "Сохранить"}
                    </button>
                </div>
            </form>
        </div>
    )
}

export default EditEventForm