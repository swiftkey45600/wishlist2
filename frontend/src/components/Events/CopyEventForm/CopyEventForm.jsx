import { useState } from "react"

function CopyEventForm({ event, onCopy, onCancel }) {
    const [title, setTitle] = useState(event.title || "")
    const [date, setDate] = useState("")
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState("")

    async function submit(formEvent) {
        formEvent.preventDefault()
        if (!title.trim() || busy) return
        setBusy(true)
        setError("")
        try {
            await onCopy(title.trim(), date)
        } catch {
            setError("Не удалось создать событие. Попробуйте ещё раз.")
        } finally {
            setBusy(false)
        }
    }

    return <div className="create-event-form">
        <h2>Создать на основе этого</h2>
        <form className="create-event-form-fields" onSubmit={submit}>
            <label className="create-event-field">Название<input value={title} onChange={event => setTitle(event.target.value)} required autoFocus /></label>
            <label className="create-event-field">Новая дата и время<input type="datetime-local" value={date} onChange={event => setDate(event.target.value)} /></label>
            {error && <p className="create-event-error" role="alert">{error}</p>}
            <div className="create-event-actions">
                <button type="button" className="create-event-secondary" onClick={onCancel} disabled={busy}>Отмена</button>
                <button type="submit" className="create-event-primary" disabled={busy}>{busy ? "Создание..." : "Создать"}</button>
            </div>
        </form>
    </div>
}

export default CopyEventForm
