import "./ConfirmDeleteModal.css"

function ConfirmDeleteModal({ itemName, onConfirm, onCancel }) {
    return (
        <div className="confirm-delete-overlay" onClick={(event) => {
            if (event.target === event.currentTarget) onCancel()
        }}>
            <div className="confirm-delete-modal" role="dialog" aria-modal="true" aria-labelledby="confirm-delete-title">
                <h2 id="confirm-delete-title">Удалить {itemName}?</h2>
                <p>Вы точно хотите удалить этот объект? Отменить действие будет невозможно.</p>
                <div className="confirm-delete-actions">
                    <button className="confirm-delete-cancel" onClick={onCancel}>
                        Отмена
                    </button>
                    <button className="confirm-delete-submit" onClick={onConfirm}>
                        Удалить
                    </button>
                </div>
            </div>
        </div>
    )
}

export default ConfirmDeleteModal