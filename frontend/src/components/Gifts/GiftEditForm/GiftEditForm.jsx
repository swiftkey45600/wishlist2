import "./GiftEditForm.css"
import { useState } from "react"

function GiftEditForm({ gift, onChange, onSave, onCancel }) {
    const [error, setError] = useState("")
    const [isSaving, setIsSaving] = useState(false)

    async function handleSubmit(event) {
        event.preventDefault()

        if (!gift.title?.trim()) {
            setError("Введите название подарка")
            return
        }

        const price = Number(gift.price)
        if (!gift.price || Number.isNaN(price) || price <= 0) {
            setError("Цена должна быть положительным числом")
            return
        }

        setError("")
        setIsSaving(true)
        const saved = await onSave()
        setIsSaving(false)

        if (!saved) setError("Не удалось сохранить подарок")
    }

    return (
        <form
            className="gift-edit-form"
            onSubmit={handleSubmit}
        >
            <h3>Редактирование подарка</h3>

            <label>
                Название
                <input
                    value={gift.title || ""}
                    onChange={e =>
                        onChange({
                            ...gift,
                            title: e.target.value
                        })
                    }
                />
            </label>

            <label>
                Цена
                <input
                    type="number"
                    value={gift.price || ""}
                    onChange={e =>
                        onChange({
                            ...gift,
                            price: e.target.value
                        })
                    }
                />
            </label>

            <label>
                Описание
                <textarea
                    value={gift.description || ""}
                    onChange={e =>
                        onChange({
                            ...gift,
                            description: e.target.value
                        })
                    }
                />
            </label>

            <label>
                Ссылка на изображение
                <input
                    value={gift.picture_url || ""}
                    onChange={e =>
                        onChange({
                            ...gift,
                            picture_url: e.target.value
                        })
                    }
                />
            </label>

            <label>
                Ссылка на маркетплейс
                <input
                    value={gift.marketplace_url || ""}
                    onChange={e =>
                        onChange({
                            ...gift,
                            marketplace_url: e.target.value
                        })
                    }
                />
            </label>

            {error && <p className="gift-edit-error">{error}</p>}

            <div className="gift-edit-actions">
                <button type="button" onClick={onCancel}>
                    Отмена
                </button>
                <button type="submit" disabled={isSaving}>
                    {isSaving ? "Сохранение..." : "Сохранить"}
                </button>
            </div>
        </form>
    )
}

export default GiftEditForm
