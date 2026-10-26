import { useEffect, useRef, useState } from "react"
import "./GiftList.css"

import GiftCard from "../GiftCard/GiftCard"
import GiftRecommendations from "../GiftRecommendations/GiftRecommendations"
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
import { resolveImageUrl, uploadImageFile } from "../../../application/imageApplication"
import { parseMarketplaceProduct } from "../../../application/marketplaceApplication"
import GiftFilters from "../GiftFilters/GiftFilters"
import { useGiftFilters } from "../GiftFilters/useGiftFilters"
import FundraisingGoalInput from "../GiftFundraising/FundraisingGoalInput"
import { parseContributionGoal } from "../../../application/contributionApplication"
import { fetchGiftsByEvent } from "../../../repositories/giftRepository"
import RecommendationSharingInput from "../GiftRecommendations/RecommendationSharingInput"
import { giftPriorityOptions } from "../giftPriority"
import {
    applySavedGiftPriorities,
    removeSavedGiftPriority,
    saveGiftPriority
} from "../../../application/giftPriorityApplication"

const ALLOWED_IMAGE_TYPES = new Set(["image/jpeg", "image/png", "image/webp", "image/gif"])

function GiftList({ eventId, isOwner, publicToken, onGiftDataChange }) {
    const [gifts, setGifts] = useState([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState(null)
    const [fieldErrors, setFieldErrors] = useState({})
    const [isFormOpen, setIsFormOpen] = useState(false)
    const [title, setTitle] = useState("")
    const [price, setPrice] = useState("")
    const [contributionGoal, setContributionGoal] = useState(null)
    const [shareInRecommendations, setShareInRecommendations] = useState(false)
    const [priority, setPriority] = useState("normal")
    const [description, setDescription] = useState("")
    const [imageFile, setImageFile] = useState(null)
    const [imagePreview, setImagePreview] = useState("")
    const [parsedImageId, setParsedImageId] = useState(null)
    const [pictureUrl, setPictureUrl] = useState("")
    const imageInputRef = useRef(null)
    const [formError, setFormError] = useState(null)
    const [marketplaceUrl, setMarketplaceUrl] = useState("")
    const [editingGift, setEditingGift] = useState(null)
    const [giftToDelete, setGiftToDelete] = useState(null)
    const [tags, setTags] = useState([])
    const [tagsLoading, setTagsLoading] = useState(true)
    const [tagsError, setTagsError] = useState("")
    const [tagsAttempt, setTagsAttempt] = useState(0)
    const [selectedTagIds, setSelectedTagIds] = useState([])
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [showReservations, setShowReservations] = useState(false)
    const [isReservationConfirmationOpen, setIsReservationConfirmationOpen] = useState(false)
    const [isParsingMarketplace, setIsParsingMarketplace] = useState(false)
    const [marketplaceNotice, setMarketplaceNotice] = useState("")

    useEffect(() => {
        return () => {
            if (imagePreview) URL.revokeObjectURL(imagePreview)
        }
    }, [imagePreview])

    useEffect(() => {
        let cancelled = false
        async function loadGifts() {
            setIsLoading(true)
            setError(null)

            try {
                const data = await getGiftsByEvent(eventId, showReservations)
                if (!cancelled) setGifts(Array.isArray(data) ? applySavedGiftPriorities(data) : [])
            } catch (loadError) {
                console.error(loadError)
                if (!cancelled) {
                    setError("Не удалось загрузить подарки")
                    setGifts([])
                }
            } finally {
                if (!cancelled) setIsLoading(false)
            }
        }

        loadGifts()
        return () => { cancelled = true }
    }, [eventId, showReservations])

    useEffect(() => {
        let cancelled = false
        async function loadTags() {
            setTags([])
            setSelectedTagIds([])
            setTagsLoading(true)
            setTagsError("")
            try {
                const data = await getEventTags(eventId)
                if (!cancelled) setTags(data)
            } catch {
                if (!cancelled) setTagsError("Не удалось загрузить теги")
            } finally {
                if (!cancelled) setTagsLoading(false)
            }
        }

        loadTags()
        return () => { cancelled = true }
    }, [eventId, tagsAttempt])

    async function handleMarketplaceAutofill() {
        const url = marketplaceUrl.trim()
        if (!url) {
            setFormError("Вставьте ссылку на товар")
            return
        }

        setFormError(null)
        setMarketplaceNotice("")
        setIsParsingMarketplace(true)
        try {
            const { product, error: parseError } = await parseMarketplaceProduct(url)
            if (!product) {
                setFormError(parseError)
                return
            }

            if (product.title) setTitle(product.title)
            if (product.price != null) setPrice(String(product.price))
            if (product.description && !description.trim()) setDescription(product.description)
            setMarketplaceUrl(product.marketplace_url || url)
            if (product.image_id || product.picture_url) {
                setImageFile(null)
                if (imageInputRef.current) imageInputRef.current.value = ""
                setPictureUrl(product.image_id ? "" : resolveImageUrl(null, product.picture_url))
                setParsedImageId(product.image_id || null)
                setImagePreview(resolveImageUrl(product.image_id, product.picture_url))
            }

            setFieldErrors(previous => ({
                ...previous,
                ...(product.title ? { title: undefined } : {}),
                ...(Number.isSafeInteger(product.price) && product.price > 0 ? { price: undefined } : {})
            }))
            const missing = []
            if (!product.title) missing.push("название")
            if (product.price == null) missing.push("цену")
            if (!product.image_id && !product.picture_url) missing.push("картинку")
            setMarketplaceNotice(product.warning || (missing.length
                ? `Не удалось получить ${missing.join(", ")}. Проверьте эти поля и заполните их вручную.`
                : "Данные получены. Проверьте их перед сохранением."))
        } finally {
            setIsParsingMarketplace(false)
        }
    }

    async function handleSubmit(event) {
        event.preventDefault()
        setFormError(null)

        const parsedPrice = Number(price)
        const errors = {}
        if (!title?.trim()) errors.title = "Введите название подарка"
        if (!Number.isSafeInteger(parsedPrice) || parsedPrice <= 0) errors.price = "Введите положительную цену в целых рублях"
        let parsedGoal
        try {
            parsedGoal = parseContributionGoal(contributionGoal)
        } catch (validationError) {
            errors.contribution_goal = validationError.message
        }
        setFieldErrors(errors)
        if (Object.keys(errors).length) return

        setIsSubmitting(true)
        try {
            let imageId = parsedImageId
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
                contribution_goal: parsedGoal,
                share_in_recommendations: shareInRecommendations,
                priority,
                description: description.trim() || undefined,
                marketplace_url: marketplaceUrl.trim() || undefined,
                image_id: imageId,
                picture_url: imageId ? null : pictureUrl.trim() || null,
                tag_ids: selectedTagIds,
                status: "available"
            })

            if (!createdGift) {
                setFormError("Не удалось создать подарок")
                return
            }

            saveGiftPriority(createdGift.id, priority)
            const selectedTags = tags.filter(tag => selectedTagIds.includes(tag.id))
            setGifts(prev => [{
                ...createdGift,
                priority,
                tags: createdGift.tags || selectedTags
            }, ...prev])
            setTitle("")
            setPrice("")
            setContributionGoal(null)
            setShareInRecommendations(false)
            setPriority("normal")
            setDescription("")
            setImageFile(null)
            setImagePreview("")
            setParsedImageId(null)
            setPictureUrl("")
            setMarketplaceUrl("")
            setSelectedTagIds([])
            setIsFormOpen(false)
            onGiftDataChange?.()
        } finally {
            setIsSubmitting(false)
        }
    }

    async function handleToggleStatus(gift) {
        let result
        if (isOwner) {
            result = await editGift(gift.id, { status: "available" })
        } else if (gift.status === "available") {
            result = await reserveGift(gift.id)
        } else if (gift.status === "bought") {
            result = await editGift(gift.id, { status: "available" })
        } else {
            result = gift.reservation_id ? await unreserveGift(gift.reservation_id) : null
        }

        if (result) {
            const updatedGifts = await getGiftsByEvent(eventId, showReservations)
            setGifts(previousGifts => Array.isArray(updatedGifts)
                ? applySavedGiftPriorities(updatedGifts).map(updatedGift => {
                    const previousGift = previousGifts.find(gift => gift.id === updatedGift.id)
                    return {
                        ...updatedGift,
                        priority: updatedGift.priority || previousGift?.priority || "normal",
                        tags: updatedGift.tags || previousGift?.tags || []
                    }
                })
                : [])
        } else {
            setError("Не удалось изменить бронь подарка")
        }
    }

    async function handleFundraisingChange() {
        const updatedGifts = await fetchGiftsByEvent(eventId, showReservations)
        setGifts(applySavedGiftPriorities(updatedGifts))
        onGiftDataChange?.()
    }

    async function handleDeleteGift() {
        if (!await deleteGift(giftToDelete.id)) {
            setError("Не удалось удалить подарок")
            return false
        }
        removeSavedGiftPriority(giftToDelete.id)
        setGifts(prev => prev.filter(gift => gift.id !== giftToDelete.id))
        setGiftToDelete(null)
        onGiftDataChange?.()
        return true
    }

    async function handleMarkBought(giftId) {
        const updated = await editGift(giftId, { status: "bought" })
        if (updated) {
            const updatedGifts = await getGiftsByEvent(eventId, showReservations)
            setGifts(Array.isArray(updatedGifts) ? applySavedGiftPriorities(updatedGifts) : [])
        }
    }

    async function handleEditGift(giftId, data) {
        const updated = await editGift(giftId, data)
        if (updated) {
            saveGiftPriority(giftId, data.priority || updated.priority || "normal")
            const selectedTags = tags.filter(tag => data.tag_ids.includes(tag.id))
            setGifts(prev => prev.map(g => g.id === giftId
                ? {
                    ...updated,
                    priority: data.priority || updated.priority || g.priority || "normal",
                    tags: updated.tags || selectedTags
                }
                : g))
            if (showReservations) {
                const refreshedGifts = await getGiftsByEvent(eventId, true)
                setGifts(Array.isArray(refreshedGifts) ? applySavedGiftPriorities(refreshedGifts) : [])
            }
            setEditingGift(null)
            onGiftDataChange?.()
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

    const { filters, filteredGifts, updateFilter } = useGiftFilters(gifts, isOwner && !showReservations)
    const isPrioritySort = filters.sortBy === "priority"
    const filteredGiftGroups = allTags
        .map(tag => ({
            tag,
            gifts: filteredGifts.filter(gift => gift.tags?.some(giftTag => giftTag.id === tag.id))
        }))
        .filter(group => group.gifts.length > 0)
    const filteredUntaggedGifts = filteredGifts.filter(gift => !gift.tags?.length)

    return (
        <div className="gift-list">
            <div className="gift-section-heading">
                <div>
                    <h2>Подарки события</h2>
                    <span>{filteredGifts.length} из {gifts.length}</span>
                </div>
                <div className="gift-section-actions">
                    {isOwner && (
                        <button
                            className="gift-reservations-toggle"
                            type="button"
                            aria-pressed={showReservations}
                            onClick={() => {
                                if (showReservations) {
                                    setShowReservations(false)
                                } else {
                                    setIsReservationConfirmationOpen(true)
                                }
                            }}
                        >
                            {showReservations ? "Скрыть брони" : "Показать брони"}
                        </button>
                    )}
                    {isOwner && <button
                        className="add-gift-button"
                        onClick={() => setIsFormOpen(prev => !prev)}
                    >
                        {isFormOpen ? "Отмена" : "+ Добавить подарок"}
                    </button>}
                </div>
            </div>

            <GiftFilters
                hideStatus={isOwner && !showReservations}
                tags={allTags}
                filters={filters}
                onFilterChange={updateFilter}
            />

            {isOwner && tagsLoading && <p role="status">Загружаем теги...</p>}
            {isOwner && tagsError && <div role="alert">
                <p>{tagsError}</p>
                <button type="button" className="gift-secondary-button"
                    onClick={() => setTagsAttempt(value => value + 1)}>Повторить загрузку тегов</button>
            </div>}

            {isOwner && isFormOpen && (
                <form className="gift-create-form gift-modal-form" onSubmit={handleSubmit} noValidate>
                    <h3>Добавить подарок</h3>
                    <div className="gift-create-row">
                        <label>
                            Название
                            <input
                                value={title}
                                aria-invalid={Boolean(fieldErrors.title)}
                                aria-describedby="create-gift-title-error"
                                onChange={e => {
                                    setTitle(e.target.value)
                                    setFieldErrors(previous => ({ ...previous, title: undefined }))
                                }}
                                placeholder="Название подарка"
                            />
                            {fieldErrors.title && <span id="create-gift-title-error" className="gift-form-error" role="alert">{fieldErrors.title}</span>}
                        </label>
                        <label>
                            Цена
                            <input
                                value={price}
                                aria-invalid={Boolean(fieldErrors.price)}
                                aria-describedby="create-gift-price-error"
                                onChange={e => {
                                    setPrice(e.target.value)
                                    setFieldErrors(previous => ({ ...previous, price: undefined }))
                                }}
                                placeholder="Цена в рублях"
                                type="number"
                            />
                            {fieldErrors.price && <span id="create-gift-price-error" className="gift-form-error" role="alert">{fieldErrors.price}</span>}
                        </label>
                        <label>
                            Приоритет
                            <select
                                value={priority}
                                onChange={event => setPriority(event.target.value)}
                            >
                                {giftPriorityOptions.map(option => (
                                    <option key={option.value} value={option.value}>{option.label}</option>
                                ))}
                            </select>
                        </label>
                    </div>

                    <FundraisingGoalInput
                        value={contributionGoal}
                        defaultGoal={price}
                        disabled={isSubmitting || isParsingMarketplace}
                        error={fieldErrors.contribution_goal}
                        onChange={value => {
                            setContributionGoal(value)
                            setFieldErrors(previous => ({ ...previous, contribution_goal: undefined }))
                        }}
                    />

                    <RecommendationSharingInput
                        checked={shareInRecommendations}
                        disabled={isSubmitting || isParsingMarketplace}
                        onChange={setShareInRecommendations}
                    />

                    <label>
                        Описание
                        <textarea
                            value={description}
                            onChange={e => setDescription(e.target.value)}
                            placeholder="Описание подарка (необязательно)"
                        />
                    </label>

                    <label>
                        Загрузить изображение файлом
                        <input
                            ref={imageInputRef}
                            disabled={isSubmitting || isParsingMarketplace}
                            type="file"
                            accept="image/jpeg,image/png,image/webp,image/gif"
                            onChange={(event) => {
                                const file = event.target.files?.[0] || null
                                if (!file) return
                                if (!ALLOWED_IMAGE_TYPES.has(file.type)) {
                                    setFormError("Выберите изображение в формате JPEG, PNG, WebP или GIF")
                                    event.target.value = ""
                                    return
                                }
                                setFormError(null)
                                setImageFile(file)
                                setPictureUrl("")
                                setParsedImageId(null)
                                setImagePreview(file ? URL.createObjectURL(file) : "")
                            }}
                        />
                    </label>
                    <label>
                        Или указать ссылку на изображение
                        <input
                            type="url"
                            pattern="https?://.+"
                            placeholder="https://example.com/photo.jpg"
                            value={pictureUrl}
                            disabled={isSubmitting || isParsingMarketplace}
                            onChange={event => {
                                const url = event.target.value
                                setPictureUrl(url)
                                setImageFile(null)
                                setParsedImageId(null)
                                if (imageInputRef.current) imageInputRef.current.value = ""
                                setFormError(null)
                                setImagePreview(/^https?:\/\//i.test(url.trim()) ? url.trim() : "")
                            }}
                        />
                    </label>
                    {imagePreview && <img className="gift-image-preview" src={imagePreview} alt="Предпросмотр подарка" />}

                    <div className="marketplace-autofill">
                        <label>
                            Ссылка на маркетплейс
                            <input
                                value={marketplaceUrl}
                                onChange={e => setMarketplaceUrl(e.target.value)}
                                placeholder="https://..."
                            />
                        </label>
                        <button
                            type="button"
                            className="gift-secondary-button"
                            onClick={handleMarketplaceAutofill}
                            disabled={isParsingMarketplace || isSubmitting}
                        >
                            {isParsingMarketplace ? "Заполняем..." : "Заполнить по ссылке"}
                        </button>
                    </div>

                    {marketplaceNotice && <p role="status">{marketplaceNotice}</p>}

                    <TagSelector
                        disabled={tagsLoading || Boolean(tagsError) || isSubmitting}
                        eventId={eventId}
                        tags={tags}
                        selectedTagIds={selectedTagIds}
                        onTagsChange={setTags}
                        onChange={setSelectedTagIds}
                    />

                    {formError && <p className="gift-form-error">{formError}</p>}

                    <div className="gift-modal-actions">
                        <button type="button" className="gift-secondary-button" onClick={() => {
                            setImageFile(null)
                            setImagePreview("")
                            setParsedImageId(null)
                            setPictureUrl("")
                            setContributionGoal(null)
                            setShareInRecommendations(false)
                            setFormError(null)
                            setIsFormOpen(false)
                        }} disabled={isSubmitting || isParsingMarketplace}>
                            Отмена
                        </button>
                        <button type="submit" className="add-gift-button" disabled={isSubmitting || isParsingMarketplace}>
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

            {!isLoading && !error && gifts.length > 0 && filteredGifts.length === 0 && (
                <p className="gift-list-status">Подарки по заданным фильтрам не найдены.</p>
            )}

            {!isLoading && !error && filteredGifts.length > 0 && isPrioritySort && (
                <div className="gift-grid">
                    {filteredGifts.map(gift => (
                        <GiftCard
                            key={gift.id}
                            gift={gift}
                            publicToken={publicToken}
                            isOwner={isOwner}
                            onGiftChange={handleFundraisingChange}
                            onToggleStatus={!isOwner || showReservations || gift.status === "available"
                                ? handleToggleStatus
                                : undefined}
                            onDelete={isOwner ? (giftId) => setGiftToDelete(gifts.find(item => item.id === giftId)) : undefined}
                            onMarkBought={isOwner && showReservations ? handleMarkBought : undefined}
                            hideReservationDetails={isOwner && !showReservations}
                            onEdit={isOwner ? openEditForm : undefined}
                        />
                    ))}
                </div>
            )}

            {!isLoading && !error && filteredGifts.length > 0 && !isPrioritySort && (
                <div className="gift-groups">
                    {filteredGiftGroups.map(group => (
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
                                        publicToken={publicToken}
                                        isOwner={isOwner}
                                        onGiftChange={handleFundraisingChange}
                                        onToggleStatus={!isOwner || (showReservations && gift.status !== "available")
                                            ? handleToggleStatus
                                            : undefined}
                                        onDelete={isOwner ? (giftId) => setGiftToDelete(gifts.find(item => item.id === giftId)) : undefined}
                                        onMarkBought={isOwner && showReservations ? handleMarkBought : undefined}
                                        hideReservationDetails={isOwner && !showReservations}
                                        onEdit={isOwner ? openEditForm : undefined}
                                    />
                                ))}
                            </div>
                        </section>
                    ))}

                    {filteredUntaggedGifts.length > 0 && (
                        <section className="gift-group">
                            <div className="gift-group-heading">
                                <h3>Без тегов</h3>
                                <span>{filteredUntaggedGifts.length}</span>
                            </div>
                            <div className="gift-grid">
                                {filteredUntaggedGifts.map(gift => (
                                    <GiftCard
                                        key={gift.id}
                                        gift={gift}
                                        publicToken={publicToken}
                                        isOwner={isOwner}
                                        onGiftChange={handleFundraisingChange}
                                        onToggleStatus={!isOwner || (showReservations && gift.status !== "available")
                                            ? handleToggleStatus
                                            : undefined}
                                        onDelete={isOwner ? (giftId) => setGiftToDelete(gifts.find(item => item.id === giftId)) : undefined}
                                        onMarkBought={isOwner && showReservations ? handleMarkBought : undefined}
                                        hideReservationDetails={isOwner && !showReservations}
                                        onEdit={isOwner ? openEditForm : undefined}
                                    />
                                ))}
                            </div>
                        </section>
                    )}
                </div>
            )}

            {isOwner && !isLoading && !error && <GiftRecommendations
                key={eventId}
                eventId={eventId}
                gifts={gifts}
                onAdd={gift => {
                    const giftWithPriority = applySavedGiftPriorities([gift])[0]
                    setGifts(previous => [giftWithPriority, ...previous])
                    onGiftDataChange?.()
                }}
            />}

            {editingGift && (
                <div className="gift-edit-modal" onClick={(event) => {
                    if (event.target === event.currentTarget) setEditingGift(null)
                }}>
                    <div className="gift-edit-dialog">
                        <GiftEditForm
                            gift={editingGift}
                            tagsDisabled={tagsLoading || Boolean(tagsError)}
                            tags={tags}
                            onTagsChange={setTags}
                            onChange={setEditingGift}
                            onSave={(imageId) =>
                                handleEditGift(editingGift.id, {
                                    title: editingGift.title.trim(),
                                    price: Number(editingGift.price),
                                    contribution_goal: parseContributionGoal(editingGift.contribution_goal, editingGift.contribution_total),
                                    share_in_recommendations: Boolean(editingGift.share_in_recommendations),
                                    description: editingGift.description?.trim() || null,
                                    picture_url: editingGift.picture_url?.trim() || null,
                                    marketplace_url: editingGift.marketplace_url?.trim() || null,
                                    priority: editingGift.priority || "normal",
                                    tag_ids: editingGift.tag_ids || [],
                                    image_id: imageId ?? null,
                                    ...(imageId ? { picture_url: null } : {})
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

            {isReservationConfirmationOpen && (
                <div
                    className="reservation-confirm-overlay"
                    onClick={(event) => {
                        if (event.target === event.currentTarget) {
                            setIsReservationConfirmationOpen(false)
                        }
                    }}
                >
                    <div
                        className="reservation-confirm-modal"
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="reservation-confirm-title"
                    >
                        <h2 id="reservation-confirm-title">Показать брони?</h2>
                        <p>Вы уверены, что хотите увидеть, какие подарки уже забронированы или куплены?</p>
                        <div className="reservation-confirm-actions">
                            <button
                                className="reservation-confirm-cancel"
                                type="button"
                                onClick={() => setIsReservationConfirmationOpen(false)}
                            >
                                Не показывать
                            </button>
                            <button
                                className="reservation-confirm-submit"
                                type="button"
                                onClick={() => {
                                    setShowReservations(true)
                                    setIsReservationConfirmationOpen(false)
                                }}
                            >
                                Показать
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default GiftList
