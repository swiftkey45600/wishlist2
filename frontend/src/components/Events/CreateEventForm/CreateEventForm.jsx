import EventDurationInput from "../EventDurationInput"
import { isValidDuration } from "../../../utils/eventDuration"
import DateTimePicker from "../DateTimePicker"
import "./CreateEventForm.css"
import { useEffect, useRef, useState } from "react"
import { isPastEventDate, todayLocalDate, withLocalOffset } from "../../../utils/eventDate"
import { uploadImageFile } from "../../../application/imageApplication"
import LocationPicker from "../LocationPicker/LocationPicker"

const allowedImageTypes = new Set(["image/jpeg", "image/png", "image/webp", "image/gif"])

function CreateEventForm({ onCreateEvent, onCancel }) {
    const [title, setTitle] = useState("")
    const [description, setDescription] = useState("")
    const [place, setPlace] = useState("")
    const [eventDate, setEventDate] = useState("")
    const [durationDays, setDurationDays] = useState(1)
    const [coverFile, setCoverFile] = useState(null)
    const coverInputRef = useRef(null)
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

        if (error === "Выберите текущие или будущие дату и время") return

        if (isPastEventDate(eventDate)) {
            setError("Выберите текущие или будущие дату и время")
            return
        }

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

            const created = await onCreateEvent({
                title: trimmedTitle,
                description: description.trim(),
                place: place.trim(),
                event_date: withLocalOffset(eventDate),
                duration_days: durationDays,
                cover_image_id: uploadedCover?.id || null
            })
            if (!created) setError("Не удалось создать событие")
        } catch (uploadError) {
            console.error("Не удалось загрузить обложку события", uploadError)
            setError("Не удалось загрузить обложку. Выберите другую или продолжите без неё.")
        } finally {
            setIsSaving(false)
        }
    }

    return (
        <div className="create-event-form">
            <h2>Создать событие</h2>
            <form className="create-event-form-fields" onSubmit={handleSubmit} noValidate>
                <label className="create-event-field">Название<input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Например, День рождения" aria-invalid={error === "Введите название события"} aria-describedby="create-event-title-error" autoFocus />
                    {error === "Введите название события" && <span id="create-event-title-error" className="create-event-error" role="alert">{error}</span>}
                </label>
                <label className="create-event-field">Описание<input value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Описание события" /></label>
                <div className="create-event-field"><span>Дата и время</span><DateTimePicker value={eventDate} min={`${todayLocalDate()}T00:00`} onChange={(event) => { setEventDate(event.target.value); if (error === "Выберите текущие или будущие дату и время") setError("") }} onBlur={() => { if (isPastEventDate(eventDate)) { setEventDate(""); setError("Выберите текущие или будущие дату и время") } }} /></div>
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
                {coverFile && <button type="button" className="event-remove-cover" onClick={() => { setCoverFile(null); setCoverPreview(""); if (coverInputRef.current) coverInputRef.current.value = ""; setError("") }}>Убрать выбранную обложку</button>}
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
