import { useEffect, useState } from "react"
import "./GiftList.css"

import GiftCard from "../GiftCard/GiftCard"
import {
  getGiftsByEvent,
  createGift,
  updateGiftStatus
} from "../../../application/giftApplication"

function GiftList({ eventId }) {
    const [gifts, setGifts] = useState([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState(null)
    const [isFormOpen, setIsFormOpen] = useState(false)
    const [title, setTitle] = useState("")
    const [price, setPrice] = useState("")
    const [description, setDescription] = useState("")
    const [imageUrl, setImageUrl] = useState("")
    const [formError, setFormError] = useState(null)

    useEffect(() => {
        if (!eventId) {
            setGifts([])
            setIsLoading(false)
            return
        }

        async function loadGifts() {
            setIsLoading(true)
            setError(null)

            try {
                const data = await getGiftsByEvent(eventId)
                setGifts(Array.isArray(data) ? data : [])
            } catch (loadError) {
                console.error(loadError)
                setError("Не удалось загрузить подарки")
                setGifts([])
            } finally {
                setIsLoading(false)
            }
        }

        loadGifts()
    }, [eventId])

    async function handleSubmit(event) {
        event.preventDefault()
        setFormError(null)

        if (!title.trim()) {
            setFormError("Название подарка обязательно")
            return
        }

        const parsedPrice = Number(price)
        if (!price || Number.isNaN(parsedPrice) || parsedPrice <= 0) {
            setFormError("Цена должна быть положительным числом")
            return
        }

        const createdGift = await createGift({
            event_id: Number(eventId),
            title: title.trim(),
            price: parsedPrice,
            description: description.trim() || undefined,
            picture_url: imageUrl.trim() || undefined,
            status: "available"
        })

        if (!createdGift) {
            setFormError("Не удалось создать подарок")
            return
        }

        setGifts(prev => [createdGift, ...prev])
        setTitle("")
        setPrice("")
        setDescription("")
        setImageUrl("")
        setIsFormOpen(false)
    }

    async function handleToggleStatus(gift) {
        const newStatus = gift.status === "available" ? "reserved" : "available"
        const updatedGift = await updateGiftStatus(gift.id, newStatus)

        if (!updatedGift) {
            setError("Не удалось обновить статус подарка")
            return
        }

        setGifts(prev => prev.map(item => item.id === gift.id ? updatedGift : item))
    }

    return (
        <div className="gift-list">
            <div className="gift-list-header">
                <h2>Подарки • {gifts.length}</h2>

                <button
                    className="add-gift-button"
                    onClick={() => setIsFormOpen(prev => !prev)}
                >
                    {isFormOpen ? "Отмена" : "+ Добавить подарок"}
                </button>
            </div>

            {isFormOpen && (
                <form className="gift-create-form" onSubmit={handleSubmit}>
                    <div className="gift-create-row">
                        <label>
                            Название
                            <input
                                value={title}
                                onChange={e => setTitle(e.target.value)}
                                placeholder="Название подарка"
                            />
                        </label>
                        <label>
                            Цена
                            <input
                                value={price}
                                onChange={e => setPrice(e.target.value)}
                                placeholder="Цена в рублях"
                                type="number"
                            />
                        </label>
                    </div>

                    <label>
                        Описание
                        <textarea
                            value={description}
                            onChange={e => setDescription(e.target.value)}
                            placeholder="Описание подарка (необязательно)"
                        />
                    </label>

                    <label>
                        Ссылка на изображение
                        <input
                            value={imageUrl}
                            onChange={e => setImageUrl(e.target.value)}
                            placeholder="https://..."
                        />
                    </label>

                    {formError && <p className="gift-form-error">{formError}</p>}

                    <button type="submit" className="add-gift-button">
                        Сохранить подарок
                    </button>
                </form>
            )}

            {isLoading && (
                <p className="gift-list-status">Загружаем подарки...</p>
            )}

            {!isLoading && error && (
                <p className="gift-list-status error">{error}</p>
            )}

            {!isLoading && !error && gifts.length === 0 && (
                <p className="gift-list-status">Пока нет подарков для этого события.</p>
            )}

            {!isLoading && !error && gifts.length > 0 && (
                <div className="gift-grid">
                    {gifts.map(gift => (
                        <GiftCard
                            key={gift.id}
                            gift={gift}
                            onToggleStatus={handleToggleStatus}
                        />
                    ))}
                </div>
            )}
        </div>
    )
}

export default GiftList
