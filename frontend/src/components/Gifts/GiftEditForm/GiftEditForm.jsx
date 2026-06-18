import "./GiftEditForm.css"

function GiftEditForm({ gift, onChange, onSave, onCancel }) {
    return (
        <form
            className="gift-edit-form"
            onSubmit={e => {
                e.preventDefault()
                onSave()
            }}
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

            <div className="gift-edit-actions">
                <button type="submit">
                    Сохранить
                </button>

                <button
                    type="button"
                    onClick={onCancel}
                >
                    Отмена
                </button>
            </div>
        </form>
    )
}

export default GiftEditForm
