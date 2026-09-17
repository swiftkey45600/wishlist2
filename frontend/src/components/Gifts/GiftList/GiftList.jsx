import { useEffect, useState } from "react"
import "./GiftList.css"

import GiftCard from "../GiftCard/GiftCard"
import {
  getGiftsByEvent,
  createGift,
  updateGiftStatus,
  deleteGift, 
  reserveGift,
  unreserveGift,
  editGift
} from "../../../application/giftApplication"

import GiftEditForm from "../GiftEditForm/GiftEditForm"

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
    const [marketplaceUrl, setMarketplaceUrl] = useState("")
    const [editingGift, setEditingGift] = useState(null)

    useEffect(() => {
        async function loadGifts() {
            if (!eventId) {
                setGifts([])
                setIsLoading(false)
                return
            }

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
            marketplace_url: marketplaceUrl.trim() || undefined,
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
        setMarketplaceUrl("")
        setIsFormOpen(false)
    }

    async function handleToggleStatus(gift) {
        if (gift.status === "available") {
            const user = JSON.parse(localStorage.getItem("user") || "null")
            await reserveGift(gift.id, user?.name ?? "Аноним")
        } else if (gift.reservation_id) {
            await unreserveGift(gift.reservation_id)
        } else {
            await updateGiftStatus(gift.id, "available")
        }

        const updated = await getGiftsByEvent(eventId)
        setGifts(Array.isArray(updated) ? updated : [])
    }

    async function handleDeleteGift(giftId) {
        await deleteGift(giftId)
        setGifts(prev => prev.filter(g => g.id !== giftId))
    }

    async function handleMarkBought(giftId) {
        const updated = await updateGiftStatus(giftId, "bought")
        if (updated) {
            setGifts(prev => prev.map(g => g.id === giftId ? updated : g))
        }
    }

    async function handleEditGift(giftId, data) {
        const updated = await editGift(giftId, data)
        if (updated) {
            setGifts(prev => prev.map(g => g.id === giftId ? updated : g))
            setEditingGift(null)
        }
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

                    <label>
                        Ссылка на маркетплейс
                        <input
                            value={marketplaceUrl}
                            onChange={e => setMarketplaceUrl(e.target.value)}
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
                            onDelete={handleDeleteGift}
                            onMarkBought={handleMarkBought}
                            onEdit={setEditingGift}
                        />
                    ))}
                </div>
            )}

            {editingGift && (
                <GiftEditForm
                    gift={editingGift}
                    onChange={setEditingGift}
                    onSave={() =>
                        handleEditGift(editingGift.id, {
                            title: editingGift.title,
                            price: Number(editingGift.price),
                            description: editingGift.description,
                            picture_url: editingGift.picture_url,
                            marketplace_url: editingGift.marketplace_url
                        })
                    }
                    onCancel={() => setEditingGift(null)}
                />
            )}
        </div>
    )
}

export default GiftList
