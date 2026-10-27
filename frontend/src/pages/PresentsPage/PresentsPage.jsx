import { useEffect, useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"

import "./PresentsPage.css"
import Header from "../../components/Header/Header"
import Sidebar from "../../components/Sidebar/Sidebar"
import { getEvents } from "../../application/eventApplication"
import {
    getGiftsByEvent,
    deleteGift,
    editGift
} from "../../application/giftApplication"
import GiftEditForm from "../../components/Gifts/GiftEditForm/GiftEditForm"
import GiftImage from "../../components/Gifts/GiftImage/GiftImage"
import { getGiftPriorityLabel } from "../../components/Gifts/giftPriority"
import {
    applySavedGiftPriorities,
    removeSavedGiftPriority,
    saveGiftPriority
} from "../../application/giftPriorityApplication"
import { getEventTags } from "../../application/tagApplication"
import { parseContributionGoal } from "../../application/contributionApplication"

function getGiftCountLabel(count) {
    if (count % 10 === 1 && count % 100 !== 11) return "подарок"
    if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return "подарка"
    return "подарков"
}

function PresentsPage() {
    const navigate = useNavigate()
    const [gifts, setGifts] = useState([])
    const [search, setSearch] = useState("")
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState(null)
    const [editingGift, setEditingGift] = useState(null)
    const [tags, setTags] = useState([])
    const [tagsLoading, setTagsLoading] = useState(false)
    const [tagsError, setTagsError] = useState("")
    const editingEventId = editingGift?.event_id

    useEffect(() => {
        if (!editingEventId) return
        let cancelled = false
        async function loadTags() {
            setTagsLoading(true)
            setTagsError("")
            setTags([])
            try {
                const data = await getEventTags(editingEventId)
                if (!cancelled) setTags(data)
            } catch {
                if (!cancelled) setTagsError("Не удалось загрузить теги события.")
            } finally {
                if (!cancelled) setTagsLoading(false)
            }
        }
        loadTags()
        return () => { cancelled = true }
    }, [editingEventId])

    useEffect(() => {
        async function loadGifts() {
            setIsLoading(true)
            setError(null)

            try {
                const loadedEvents = await getEvents()
                const eventList = Array.isArray(loadedEvents) ? loadedEvents : []
                const giftGroups = await Promise.all(
                    eventList.map(async (event) => {
                        const eventGifts = await getGiftsByEvent(event.id)
                        return (Array.isArray(eventGifts) ? eventGifts : []).map((gift) => ({
                            ...gift,
                            event,
                        }))
                    })
                )

                setGifts(applySavedGiftPriorities(giftGroups.flat()))
            } catch (loadError) {
                console.error(loadError)
                setError("Не удалось загрузить подарки")
            } finally {
                setIsLoading(false)
            }
        }

        loadGifts()
    }, [])

    const filteredGifts = useMemo(() => {
        const query = search.trim().toLowerCase()

        return gifts.filter((gift) => {
            const matchesSearch = !query || gift.title?.toLowerCase().includes(query)
            return matchesSearch
        })
    }, [gifts, search])

    async function handleDelete(giftId) {
        if (!await deleteGift(giftId)) {
            setError("Не удалось удалить подарок. Попробуйте ещё раз.")
            return
        }
        removeSavedGiftPriority(giftId)
        setError(null)
        setGifts((currentGifts) => currentGifts.filter((gift) => gift.id !== giftId))
    }

    async function handleEdit(giftId, data) {
        const updatedGift = await editGift(giftId, data)
        if (!updatedGift) return false

        saveGiftPriority(giftId, data.priority || updatedGift.priority || "normal")
        setGifts((currentGifts) => currentGifts.map((gift) => (
            gift.id === giftId
                ? { ...updatedGift, priority: data.priority || updatedGift.priority || gift.priority || "normal", event: gift.event }
                : gift
        )))
        setEditingGift(null)
        return true
    }

    return (
        <div className="presents-shell">
            <Header />

            <div className="page-layout presents-layout">
                <Sidebar />

                <main className="page-content presents-content">
                    <div className="presents-heading">
                        <div>
                            <h1>Мои подарки</h1>
                            <div className="presents-muted">Все подарки из ваших событий в одном месте</div>
                        </div>

                        <button className="presents-button primary" onClick={() => navigate("/")}>
                            ＋ Добавить подарок
                        </button>
                    </div>

                    <div className="presents-toolbar">
                        <div className="presents-search">
                            <span aria-hidden="true">⌕</span>

                            <input
                                value={search}
                                onChange={(event) => setSearch(event.target.value)}
                                placeholder="Поиск по названию подарка..."
                            />
                        </div>

                    </div>

                    <div className="presents-section-title">
                        <h2>Подарки</h2>
                        <span>{filteredGifts.length} {getGiftCountLabel(filteredGifts.length)}</span>
                    </div>

                    {isLoading && <p className="presents-status">Загружаем подарки...</p>}
                    {error && <p className="presents-status error-text">{error}</p>}
                    {!isLoading && !error && filteredGifts.length === 0 && (
                        <p className="presents-status">Подарки не найдены.</p>
                    )}

                    {!isLoading && filteredGifts.length > 0 && (
                        <div className="presents-grid">
                            {filteredGifts.map((gift) => (
                                <article
                                    className="presents-gift-card"
                                    key={gift.id}
                                    onClick={() => navigate(`/events/${gift.event.id}`)}
                                >
                                    <div className="presents-gift-top">
                                        <GiftImage
                                            gift={gift}
                                            className="presents-pic"
                                            fallbackClassName="presents-pic presents-pic-fallback"
                                        />
                                        <div>
                                            <div className="presents-gift-title">
                                                <h3>{gift.title}</h3>
                                                {gift.priority === "high" && (
                                                    <span className="gift-priority-badge">
                                                        {getGiftPriorityLabel(gift.priority)}
                                                    </span>
                                                )}
                                                {gift.tags?.length > 0 && (
                                                    <div className="presents-gift-tags">
                                                        {gift.tags.slice(0, 3).map(tag => (
                                                            <span className="presents-gift-tag" key={tag.id}>
                                                                {tag.name}
                                                            </span>
                                                        ))}
                                                        {gift.tags.length > 3 && (
                                                            <span className="presents-tag-overflow">
                                                                <button
                                                                    type="button"
                                                                    className="presents-gift-tag presents-gift-tag-more"
                                                                    aria-label={`${gift.tags.length - 3} скрытых тегов`}
                                                                    aria-describedby={`presents-hidden-tags-${gift.id}`}
                                                                >
                                                                    +{gift.tags.length - 3}
                                                                </button>
                                                                <span className="presents-hidden-tags" id={`presents-hidden-tags-${gift.id}`} role="tooltip">
                                                                    {gift.tags.slice(3).map(tag => (
                                                                        <span className="presents-hidden-tag" key={tag.id}>
                                                                            {tag.name}
                                                                        </span>
                                                                    ))}
                                                                </span>
                                                            </span>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                            <button
                                                className="presents-event-link"
                                                onClick={(event) => {
                                                    event.stopPropagation()
                                                    navigate(`/events/${gift.event.id}`)
                                                }}
                                            >
                                                {gift.event.title}
                                            </button>
                                            <p className="presents-description">
                                                {gift.description || "Описание подарка пока не добавлено."}
                                            </p>
                                            <strong className="presents-price">{gift.price} ₽</strong>
                                        </div>
                                    </div>
                                    <div className="presents-gift-bottom">
                                        {gift.marketplace_url && (
                                            <span className="presents-market">🛍 Подключён</span>
                                        )}
                                        <div className="presents-actions">
                                            <div className="presents-manage-actions">
                                                <button className="presents-button secondary" onClick={(event) => {
                                                    event.stopPropagation()
                                                    setEditingGift({ ...gift, tag_ids: gift.tags?.map(tag => tag.id) || [] })
                                                }}>
                                                    Изменить
                                                </button>

                                                <button className="presents-button danger" onClick={(event) => {
                                                    event.stopPropagation()
                                                    handleDelete(gift.id)
                                                }}>
                                                    Удалить
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </article>
                            ))}
                        </div>
                    )}

                    {editingGift && (
                        <div className="presents-edit-modal" onClick={(event) => {
                            if (event.target === event.currentTarget) setEditingGift(null)
                        }}>
                            <div className="presents-edit-dialog">
                                {tagsError && <p role="alert">{tagsError}</p>}
                                <GiftEditForm
                                    gift={editingGift}
                                    tags={tags}
                                    tagsDisabled={tagsLoading || Boolean(tagsError)}
                                    onTagsChange={setTags}
                                    onChange={setEditingGift}
                                    onSave={(imageId) => handleEdit(editingGift.id, {
                                        title: editingGift.title.trim(),
                                        price: Number(editingGift.price),
                                        contribution_goal: parseContributionGoal(editingGift.contribution_goal, editingGift.contribution_total),
                                        share_in_recommendations: Boolean(editingGift.share_in_recommendations),
                                        tag_ids: editingGift.tag_ids,
                                        description: editingGift.description?.trim() || null,
                                        picture_url: editingGift.picture_url?.trim() || null,
                                        marketplace_url: editingGift.marketplace_url?.trim() || null,
                                        priority: editingGift.priority || "normal",
                                        image_id: imageId ?? null,
                                        ...(imageId ? { picture_url: null } : {})
                                    })}
                                    onCancel={() => setEditingGift(null)}
                                />
                            </div>
                        </div>
                    )}
                </main>
            </div>
        </div>
    )
}

export default PresentsPage
