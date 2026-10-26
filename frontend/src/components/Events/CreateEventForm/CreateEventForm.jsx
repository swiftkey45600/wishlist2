import "./CreateEventForm.css"
import { useEffect, useState } from "react"
import { uploadImageFile } from "../../../application/imageApplication"

const allowedImageTypes = new Set(["image/jpeg", "image/png", "image/webp", "image/gif"])

function CreateEventForm({ onCreateEvent, onCancel }) {
    const [title, setTitle] = useState("")
    const [description, setDescription] = useState("")
    const [place, setPlace] = useState("")
    const [eventDate, setEventDate] = useState("")
    const [coverFile, setCoverFile] = useState(null)
    const [coverPreview, setCoverPreview] = useState("")
    const [error, setError] = useState("")
    const [isSaving, setIsSaving] = useState(false)

    useEffect(() => {
        if (!coverPreview.startsWith("blob:")) return
        return () => URL.revokeObjectURL(coverPreview)
    }, [coverPreview])

    async function handleSubmit(event) {
        event.preventDefault()
        const trimmedTitle = title.trim()

        if (!trimmedTitle) {
            setError("Введите название события")
            return
        }

        setError("")
        setIsSaving(true)
        try {
            const uploadedCover = coverFile ? await uploadImageFile(coverFile) : null
            if (coverFile && !uploadedCover?.id) {
                setError("Не удалось загрузить обложку")
                return
            }

            const created = await onCreateEvent({
                title: trimmedTitle,
                description: description.trim(),
                place: place.trim(),
                event_date: eventDate,
                cover_image_id: uploadedCover?.id || null
            })
            if (!created) setError("Не удалось создать событие")
        } catch (uploadError) {
            console.error("Не удалось загрузить обложку события", uploadError)
            setError("Не удалось загрузить обложку")
        } finally {
            setIsSaving(false)
        }
    }

    return (
        <div className="create-event-form">
            <h2>Создать событие</h2>
            <form className="create-event-form-fields" onSubmit={handleSubmit}>
                <label className="create-event-field">Название<input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Например, День рождения" aria-invalid={error === "Введите название события"} aria-describedby="create-event-title-error" autoFocus />
                    {error === "Введите название события" && <span id="create-event-title-error" className="create-event-error" role="alert">{error}</span>}
                </label>
                <label className="create-event-field">Описание<input value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Описание события" /></label>
                <label className="create-event-field">Дата и время<input value={eventDate} type="datetime-local" onChange={(event) => setEventDate(event.target.value)} /></label>
                <label className="create-event-field">Место<input value={place} onChange={(event) => setPlace(event.target.value)} placeholder="Город или место" /></label>
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
                {error && error !== "Введите название события" && <p className="create-event-error" role="alert">{error}</p>}
                <div className="create-event-actions">
                    <button type="button" className="create-event-secondary" onClick={onCancel} disabled={isSaving}>Отмена</button>
                    <button type="submit" className="create-event-primary" disabled={isSaving}>{isSaving ? "Создание..." : "Создать"}</button>
                </div>
            </form>
        </div>
    )
}

export default CreateEventForm
