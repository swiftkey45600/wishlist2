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
import TagSelector from "../../Tags/TagSelector/TagSelector"
import { getEventTags } from "../../../application/tagApplication"

function GiftList({ eventId, isOwner }) {
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
    const [giftToDelete, setGiftToDelete] = useState(null)
    const [tags, setTags] = useState([])
    const [selectedTagIds, setSelectedTagIds] = useState([])

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

    useEffect(() => {
        async function loadTags() {
            const data = await getEventTags(eventId)
            setTags(Array.isArray(data) ? data : [])
        }

        loadTags()
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
            tag_ids: selectedTagIds,
            status: "available"
        })

        if (!createdGift) {
            setFormError("Не удалось создать подарок")
            return
        }

        const selectedTags = tags.filter(tag => selectedTagIds.includes(tag.id))
        setGifts(prev => [{
            ...createdGift,
            tags: createdGift.tags || selectedTags
        }, ...prev])
        setTitle("")
        setPrice("")
        setDescription("")
        setImageUrl("")
        setMarketplaceUrl("")
        setSelectedTagIds([])
        setIsFormOpen(false)
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
            setGifts(previousGifts => Array.isArray(updatedGifts)
                ? updatedGifts.map(updatedGift => ({
                    ...updatedGift,
                    tags: updatedGift.tags || previousGifts.find(gift => gift.id === updatedGift.id)?.tags || []
                }))
                : [])
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
            setGifts(prev => prev.map(g => g.id === giftId
                ? { ...updated, tags: updated.tags || g.tags || [] }
                : g))
        }
    }

    async function handleEditGift(giftId, data) {
        const updated = await editGift(giftId, data)
        if (updated) {
            const selectedTags = tags.filter(tag => data.tag_ids.includes(tag.id))
            setGifts(prev => prev.map(g => g.id === giftId
                ? { ...updated, tags: updated.tags || selectedTags }
                : g))
            setEditingGift(null)
            return true
        }

        return false
    }

    function openEditForm(gift) {
        setEditingGift({
            ...gift,
            tag_ids: gift.tags?.map(tag => tag.id) || []
        })
    }

    const allTags = [...tags]
    gifts.forEach(gift => {
        gift.tags?.forEach(tag => {
            if (!allTags.some(existingTag => existingTag.id === tag.id)) {
                allTags.push(tag)
            }
        })
    })

    const giftGroups = allTags
        .map(tag => ({
            tag,
            gifts: gifts.filter(gift => gift.tags?.some(giftTag => giftTag.id === tag.id))
        }))
        .filter(group => group.gifts.length > 0)

    const untaggedGifts = gifts.filter(gift => !gift.tags?.length)

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

                    <TagSelector
                        eventId={eventId}
                        tags={tags}
                        selectedTagIds={selectedTagIds}
                        onTagsChange={setTags}
                        onChange={setSelectedTagIds}
                    />

                    {formError && <p className="gift-form-error">{formError}</p>}

                    <div className="gift-modal-actions">
                        <button type="button" className="gift-secondary-button" onClick={() => setIsFormOpen(false)}>
                            Отмена
                        </button>
                        <button type="submit" className="add-gift-button">Добавить</button>
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
                <div className="gift-groups">
                    {giftGroups.map(group => (
                        <section className="gift-group" key={group.tag.id}>
                            <div className="gift-group-heading">
                                <h3>{group.tag.name}</h3>
                                <span>{group.gifts.length}</span>
                            </div>
                            <div className="gift-grid">
                                {group.gifts.map(gift => (
                                    <GiftCard
                                        key={`${group.tag.id}-${gift.id}`}
                                        gift={gift}
                                        onToggleStatus={handleToggleStatus}
                                        onDelete={isOwner ? (giftId) => setGiftToDelete(gifts.find(item => item.id === giftId)) : undefined}
                                        onMarkBought={isOwner ? handleMarkBought : undefined}
                                        onEdit={isOwner ? openEditForm : undefined}
                                    />
                                ))}
                            </div>
                        </section>
                    ))}

                    {untaggedGifts.length > 0 && (
                        <section className="gift-group">
                            <div className="gift-group-heading">
                                <h3>Без тегов</h3>
                                <span>{untaggedGifts.length}</span>
                            </div>
                            <div className="gift-grid">
                                {untaggedGifts.map(gift => (
                                    <GiftCard
                                        key={gift.id}
                                        gift={gift}
                                        onToggleStatus={handleToggleStatus}
                                        onDelete={isOwner ? (giftId) => setGiftToDelete(gifts.find(item => item.id === giftId)) : undefined}
                                        onMarkBought={isOwner ? handleMarkBought : undefined}
                                        onEdit={isOwner ? openEditForm : undefined}
                                    />
                                ))}
                            </div>
                        </section>
                    )}
                </div>
            )}

            {editingGift && (
                <div className="gift-edit-modal" onClick={(event) => {
                    if (event.target === event.currentTarget) setEditingGift(null)
                }}>
                    <div className="gift-edit-dialog">
                        <GiftEditForm
                            gift={editingGift}
                            tags={tags}
                            onTagsChange={setTags}
                            onChange={setEditingGift}
                            onSave={() =>
                                handleEditGift(editingGift.id, {
                                    title: editingGift.title.trim(),
                                    price: Number(editingGift.price),
                                    description: editingGift.description?.trim() || null,
                                    picture_url: editingGift.picture_url?.trim() || null,
                                    marketplace_url: editingGift.marketplace_url?.trim() || null,
                                    tag_ids: editingGift.tag_ids || []
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
