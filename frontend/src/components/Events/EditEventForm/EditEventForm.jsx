import EventDurationInput from "../EventDurationInput"
import { getEventDurationDays, isValidDuration } from "../../../utils/eventDuration"
import DateTimePicker from "../DateTimePicker"
import { useEffect, useRef, useState } from "react"
import "../CreateEventForm/CreateEventForm.css"
import { isPastEventDate, todayLocalDate } from "../../../utils/eventDate"
import { resolveImageUrl, uploadImageFile } from "../../../application/imageApplication"
import LocationPicker from "../LocationPicker/LocationPicker"

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
    const [durationDays, setDurationDays] = useState(event.duration_days || getEventDurationDays(event.event_date, event.end_date))
    const [coverFile, setCoverFile] = useState(null)
    const coverInputRef = useRef(null)
    const [coverPreview, setCoverPreview] = useState(
        resolveImageUrl(event.cover_image_id, event.cover_image_url || event.cover_url)
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

        if (error === "Выберите текущие или будущие дату и время") return

        if (eventDate !== getDateTimeValue(event.event_date) && isPastEventDate(eventDate)) {
            setError("Выберите текущие или будущие дату и время")
            return
        }

        setTitleError("")
        if (!isValidDuration(durationDays)) {
            setError("Укажите длительность от 1 до 3650 дней")
            return
        }

        if (!eventDate && durationDays > 1) { setError("Укажите дату начала для события на несколько дней"); return }
        setError("")
        setIsSaving(true)
        try {
            const uploadedCover = coverFile ? await uploadImageFile(coverFile) : null
            if (coverFile && !uploadedCover?.id) {
                setError("Не удалось загрузить обложку. Выберите другую или продолжите без неё.")
                return
            }

            const saved = await onSave({
                title: title.trim(),
                description: description.trim(),
                place: place.trim(),
                event_date: eventDate || null,
                duration_days: durationDays,
                ...(uploadedCover ? { cover_image_id: uploadedCover.id } : {})
            })
            if (!saved) setError("Не удалось сохранить изменения")
        } catch (uploadError) {
            console.error("Не удалось загрузить обложку события", uploadError)
            setError("Не удалось загрузить обложку. Выберите другую или продолжите без неё.")
        } finally {
            setIsSaving(false)
        }
    }

    return (
        <div className="create-event-form">
            <h2>Редактировать событие</h2>
            <form className="create-event-form-fields" onSubmit={handleSubmit} noValidate>
                <label className="create-event-field">
                    Название
                    <input value={title} onChange={(inputEvent) => setTitle(inputEvent.target.value)} aria-invalid={Boolean(titleError)} aria-describedby="edit-event-title-error" autoFocus />
                    {titleError && <span id="edit-event-title-error" className="create-event-error" role="alert">{titleError}</span>}
                </label>
                <label className="create-event-field">
                    Описание
                    <textarea value={description} onChange={(inputEvent) => setDescription(inputEvent.target.value)} />
                </label>
                <div className="create-event-field">
                    <span>Дата и время</span>
                    <DateTimePicker value={eventDate} min={`${todayLocalDate()}T00:00`} onChange={(inputEvent) => { setEventDate(inputEvent.target.value); if (error === "Выберите текущие или будущие дату и время") setError("") }} onBlur={() => { if (eventDate !== getDateTimeValue(event.event_date) && isPastEventDate(eventDate)) { setEventDate(getDateTimeValue(event.event_date)); setError("Выберите текущие или будущие дату и время") } }} />
                </div>
                <EventDurationInput startDate={eventDate} value={durationDays} onChange={setDurationDays} />
                <LocationPicker value={place} onChange={setPlace} />
                <label className="create-event-field">
                    Обложка события
                    <span className="event-cover-picker"><span>Выбрать фото</span><input
                        type="file"
                        ref={coverInputRef}
                        accept="image/jpeg,image/png,image/webp,image/gif"
                        disabled={isSaving}
                        onChange={(inputEvent) => {
                            const file = inputEvent.target.files?.[0] || null
                            if (!file) return
                            if (file.size > 5 * 1024 * 1024) {
                                setError("Изображение должно быть не больше 5 МБ")
                                inputEvent.target.value = ""
                                return
                            }
                            if (!allowedImageTypes.has(file.type)) {
                                setError("Выберите изображение в формате JPEG, PNG, WebP или GIF")
                                inputEvent.target.value = ""
                                return
                            }
                            setError("")
                            setCoverFile(file)
                            setCoverPreview(URL.createObjectURL(file))
                        }}
                    /></span>
                    <span className="event-cover-hint">{coverFile ? coverFile.name : "Фото из файлов или галереи, до 5 МБ"}</span>
                </label>
                {coverPreview && <img className="event-cover-preview" src={coverPreview} alt="Предпросмотр обложки события" />}
                {coverFile && <button type="button" className="event-remove-cover" onClick={() => { setCoverFile(null); setCoverPreview(resolveImageUrl(event.cover_image_id, event.cover_image_url || event.cover_url)); if (coverInputRef.current) coverInputRef.current.value = ""; setError("") }}>Убрать выбранную обложку</button>}
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