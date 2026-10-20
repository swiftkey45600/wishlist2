import "./ConfirmDeleteModal.css"
import { useState } from "react"

function ConfirmDeleteModal({ itemName, onConfirm, onCancel }) {
    const [pending, setPending] = useState(false)
    const [error, setError] = useState("")
    async function confirm() {
        if (pending) return
        setPending(true)
        setError("")
        try {
            if (await onConfirm() === false) setError("Не удалось удалить. Попробуйте ещё раз.")
        } catch {
            setError("Не удалось удалить. Попробуйте ещё раз.")
        } finally {
            setPending(false)
        }
    }
    return (
        <div className="confirm-delete-overlay" onClick={(event) => {
            if (!pending && event.target === event.currentTarget) onCancel()
        }}>
            <div className="confirm-delete-modal" role="dialog" aria-modal="true" aria-labelledby="confirm-delete-title">
                <h2 id="confirm-delete-title">Удалить {itemName}?</h2>
                <p>Вы точно хотите удалить этот объект? Отменить действие будет невозможно.</p>
                {error && <p role="alert">{error}</p>}
                <div className="confirm-delete-actions">
                    <button className="confirm-delete-cancel" onClick={onCancel} disabled={pending}>
                        Отмена
                    </button>
                    <button className="confirm-delete-submit" onClick={confirm} disabled={pending}>
                        {pending ? "Удаляем..." : "Удалить"}
                    </button>
                </div>
            </div>
        </div>
    )
}

export default ConfirmDeleteModal
