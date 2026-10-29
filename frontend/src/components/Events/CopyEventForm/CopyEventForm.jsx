import DateTimePicker from "../DateTimePicker"
import { useRef, useState } from "react"
import { isPastEventDate, todayLocalDate } from "../../../utils/eventDate"

function CopyEventForm({ event, onCopy, onCancel }) {
    const [title, setTitle] = useState(event.title || "")
    const [date, setDate] = useState("")
    const [busy, setBusy] = useState(false)
    const pending = useRef(false)
    const [error, setError] = useState("")

    async function submit(formEvent) {
        formEvent.preventDefault()
        if (!title.trim() || pending.current) return
        if (error === "Выберите сегодняшнюю или будущую дату") return

        if (isPastEventDate(date)) {
            setError("Выберите сегодняшнюю или будущую дату")
            return
        }
        pending.current = true
        setBusy(true)
        setError("")
        try {
            await onCopy(title.trim(), date)
        } catch {
            setError("Не удалось подтвердить создание. Проверьте список событий перед повторной попыткой.")
        } finally {
            pending.current = false
            setBusy(false)
        }
    }

    return <div className="create-event-form">
        <h2>Создать на основе этого</h2>
        <form className="create-event-form-fields" onSubmit={submit} noValidate>
            <label className="create-event-field">Название<input value={title} onChange={event => setTitle(event.target.value)} required autoFocus /></label>
            <label className="create-event-field">Новая дата и время<DateTimePicker min={`${todayLocalDate()}T00:00`} value={date} onChange={event => { setDate(event.target.value); if (error === "Выберите сегодняшнюю или будущую дату") setError("") }} onBlur={() => { if (isPastEventDate(date)) { setDate(""); setError("Выберите сегодняшнюю или будущую дату") } }} /></label>
            {error && <p className="create-event-error" role="alert">{error}</p>}
            <div className="create-event-actions">
                <button type="button" className="create-event-secondary" onClick={onCancel} disabled={busy}>Отмена</button>
                <button type="submit" className="create-event-primary" disabled={busy}>{busy ? "Создание..." : "Создать"}</button>
            </div>
        </form>
    </div>
}

export default CopyEventForm
