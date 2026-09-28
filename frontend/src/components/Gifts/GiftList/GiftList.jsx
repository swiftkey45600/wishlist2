import { useEffect, useState } from "react"
import "./GiftList.css"

import GiftCard from "../GiftCard/GiftCard"
import {
  getGiftsByEvent,
  createGift,
  deleteGift, 
    editGift,
    reserveGift,
    unreserveGift
} from "../../../application/giftApplication"

import GiftEditForm from "../GiftEditForm/GiftEditForm"
import ConfirmDeleteModal from "../../ConfirmDeleteModal/ConfirmDeleteModal"
import { uploadImageFile } from "../../../application/imageApplication"

const ALLOWED_IMAGE_TYPES = new Set(["image/jpeg", "image/png", "image/webp", "image/gif"])

function GiftList({ eventId, isOwner }) {
    const [gifts, setGifts] = useState([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState(null)
    const [isFormOpen, setIsFormOpen] = useState(false)
    const [title, setTitle] = useState("")
    const [price, setPrice] = useState("")
    const [description, setDescription] = useState("")
    const [imageFile, setImageFile] = useState(null)
    const [imagePreview, setImagePreview] = useState("")
    const [formError, setFormError] = useState(null)
    const [marketplaceUrl, setMarketplaceUrl] = useState("")
    const [editingGift, setEditingGift] = useState(null)
    const [giftToDelete, setGiftToDelete] = useState(null)
    const [isSubmitting, setIsSubmitting] = useState(false)

    useEffect(() => {
        return () => {
            if (imagePreview) URL.revokeObjectURL(imagePreview)
        }
    }, [imagePreview])

    useEffect(() => {
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

        setIsSubmitting(true)
        try {
            let imageId
            if (imageFile) {
                const uploadedImage = await uploadImageFile(imageFile)
                if (!uploadedImage?.id) {
                    setFormError("Не удалось загрузить изображение")
                    return
                }
                imageId = uploadedImage.id
            }

            const createdGift = await createGift({
                event_id: Number(eventId),
                title: title.trim(),
                price: parsedPrice,
                description: description.trim() || undefined,
                marketplace_url: marketplaceUrl.trim() || undefined,
                image_id: imageId,
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
            setImageFile(null)
            setMarketplaceUrl("")
            setIsFormOpen(false)
        } finally {
            setIsSubmitting(false)
        }
    }

    async function handleToggleStatus(gift) {
        let result
        if (gift.status === "available") {
            result = await reserveGift(gift.id)
        } else if (gift.status === "bought") {
            result = await editGift(gift.id, { status: "available" })
        } else {
            result = gift.reservation_id ? await unreserveGift(gift.reservation_id) : null
        }

        if (result) {
            const updatedGifts = await getGiftsByEvent(eventId)
            setGifts(Array.isArray(updatedGifts) ? updatedGifts : [])
        } else {
            setError("Не удалось изменить бронь подарка")
        }
    }

    async function handleDeleteGift() {
        await deleteGift(giftToDelete.id)
        setGifts(prev => prev.filter(gift => gift.id !== giftToDelete.id))
        setGiftToDelete(null)
    }

    async function handleMarkBought(giftId) {
        const updated = await editGift(giftId, { status: "bought" })
        if (updated) {
            setGifts(prev => prev.map(g => g.id === giftId ? updated : g))
        }
    }

    async function handleEditGift(giftId, data) {
        const updated = await editGift(giftId, data)
        if (updated) {
            setGifts(prev => prev.map(g => g.id === giftId ? updated : g))
            setEditingGift(null)
            return true
        }

        return false
    }

    return (
        <div className="gift-list">
            <div className="gift-section-heading">
                <div>
                    <h2>Подарки события</h2>
                    <span>{gifts.length} подарка</span>
                </div>
                {isOwner && <button
                    className="add-gift-button"
                    onClick={() => setIsFormOpen(prev => !prev)}
                >
                    {isFormOpen ? "Отмена" : "+ Добавить подарок"}
                </button>}
            </div>

            {isOwner && isFormOpen && (
                <form className="gift-create-form gift-modal-form" onSubmit={handleSubmit}>
                    <h3>Добавить подарок</h3>
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
                        Изображение подарка
                        <input
                            type="file"
                            accept="image/jpeg,image/png,image/webp,image/gif"
                            onChange={(event) => {
                                const file = event.target.files?.[0] || null
                                if (file && !ALLOWED_IMAGE_TYPES.has(file.type)) {
                                    setFormError("Выберите изображение в формате JPEG, PNG, WebP или GIF")
                                    event.target.value = ""
                                    return
                                }
                                setFormError(null)
                                setImageFile(file)
                                setImagePreview(file ? URL.createObjectURL(file) : "")
                            }}
                        />
                    </label>
                    {imagePreview && <img className="gift-image-preview" src={imagePreview} alt="Предпросмотр подарка" />}

                    <label>
                        Ссылка на маркетплейс
                        <input
                            value={marketplaceUrl}
                            onChange={e => setMarketplaceUrl(e.target.value)}
                            placeholder="https://..."
                        />
                    </label>

                    {formError && <p className="gift-form-error">{formError}</p>}

                    <div className="gift-modal-actions">
                        <button type="button" className="gift-secondary-button" onClick={() => {
                            setImageFile(null)
                            setFormError(null)
                            setIsFormOpen(false)
                        }} disabled={isSubmitting}>
                            Отмена
                        </button>
                        <button type="submit" className="add-gift-button" disabled={isSubmitting}>
                            {isSubmitting ? "Загрузка..." : "Добавить"}
                        </button>
                    </div>
                </form>
            )}

            {isLoading && (
                <p className="gift-list-status">Загружаем подарки...</p>
            )}

            {!isLoading && error && (
                <p className="gift-list-status error">{error}</p>
            )}

            {!isLoading && !error && gifts.length === 0 && (
                <p className="gift-list-status">Подарки не найдены.</p>
            )}

            {!isLoading && !error && gifts.length > 0 && (
                <div className="gift-grid">
                    {gifts.map(gift => (
                        <GiftCard
                            key={gift.id}
                            gift={gift}
                            onToggleStatus={handleToggleStatus}
                            onDelete={isOwner ? (giftId) => setGiftToDelete(gifts.find(gift => gift.id === giftId)) : undefined}
                            onMarkBought={isOwner ? handleMarkBought : undefined}
                            onEdit={isOwner ? setEditingGift : undefined}
                        />
                    ))}
                </div>
            )}

            {editingGift && (
                <div className="gift-edit-modal" onClick={(event) => {
                    if (event.target === event.currentTarget) setEditingGift(null)
                }}>
                    <div className="gift-edit-dialog">
                        <GiftEditForm
                            gift={editingGift}
                            onChange={setEditingGift}
                            onSave={(imageId) =>
                                handleEditGift(editingGift.id, {
                                    title: editingGift.title.trim(),
                                    price: Number(editingGift.price),
                                    description: editingGift.description?.trim() || null,
                                    picture_url: editingGift.picture_url?.trim() || null,
                                    marketplace_url: editingGift.marketplace_url?.trim() || null,
                                    ...(imageId ? { image_id: imageId, picture_url: null } : {})
                                })
                            }
                            onCancel={() => setEditingGift(null)}
                        />
                    </div>
                </div>
            )}

            {giftToDelete && (
                <ConfirmDeleteModal
                    itemName="подарок"
                    onConfirm={handleDeleteGift}
                    onCancel={() => setGiftToDelete(null)}
                />
            )}
        </div>
    )
}

export default GiftList
