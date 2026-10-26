import { useEffect, useState } from "react"
import "../CreateEventForm/CreateEventForm.css"
import { resolveImageUrl, uploadImageFile } from "../../../application/imageApplication"

const allowedImageTypes = new Set(["image/jpeg", "image/png", "image/webp", "image/gif"])

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
    const [coverFile, setCoverFile] = useState(null)
    const [coverPreview, setCoverPreview] = useState(
        resolveImageUrl(event.cover_image_id, event.cover_url || event.cover_image_url)
    )
    const [error, setError] = useState("")
    const [titleError, setTitleError] = useState("")
    const [isSaving, setIsSaving] = useState(false)

    useEffect(() => {
        if (!coverPreview.startsWith("blob:")) return
        return () => URL.revokeObjectURL(coverPreview)
    }, [coverPreview])

    async function handleSubmit(submitEvent) {
        submitEvent.preventDefault()

        if (!title.trim()) {
            setTitleError("Введите название события")
            return
        }

        setTitleError("")
        setError("")
        setIsSaving(true)
        try {
            const uploadedCover = coverFile ? await uploadImageFile(coverFile) : null
            if (coverFile && !uploadedCover?.id) {
                setError("Не удалось загрузить обложку")
                return
            }

            const saved = await onSave({
                title: title.trim(),
                description: description.trim(),
                place: place.trim(),
                event_date: eventDate || null,
                ...(uploadedCover ? { cover_image_id: uploadedCover.id } : {})
            })
            if (!saved) setError("Не удалось сохранить изменения")
        } catch (uploadError) {
            console.error("Не удалось загрузить обложку события", uploadError)
            setError("Не удалось загрузить обложку")
        } finally {
            setIsSaving(false)
        }
    }

    return (
        <div className="create-event-form">
            <h2>Редактировать событие</h2>
            <form className="create-event-form-fields" onSubmit={handleSubmit}>
                <label className="create-event-field">
                    Название
                    <input value={title} onChange={(inputEvent) => setTitle(inputEvent.target.value)} aria-invalid={Boolean(titleError)} aria-describedby="edit-event-title-error" autoFocus />
                    {titleError && <span id="edit-event-title-error" className="create-event-error" role="alert">{titleError}</span>}
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
                <label className="create-event-field">
                    Обложка события
                    <input
                        type="file"
                        accept="image/jpeg,image/png,image/webp,image/gif"
                        disabled={isSaving}
                        onChange={(inputEvent) => {
                            const file = inputEvent.target.files?.[0] || null
                            if (!file) return
                            if (!allowedImageTypes.has(file.type)) {
                                setError("Выберите изображение в формате JPEG, PNG, WebP или GIF")
                                inputEvent.target.value = ""
                                return
                            }
                            setError("")
                            setCoverFile(file)
                            setCoverPreview(URL.createObjectURL(file))
                        }}
                    />
                </label>
                {coverPreview && <img className="event-cover-preview" src={coverPreview} alt="Предпросмотр обложки события" />}
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