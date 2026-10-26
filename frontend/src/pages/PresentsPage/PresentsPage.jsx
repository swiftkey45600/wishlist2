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
                                            <h3>{gift.title}</h3>
                                            {gift.priority === "high" && (
                                                <span className="gift-priority-badge">
                                                    {getGiftPriorityLabel(gift.priority)}
                                                </span>
                                            )}
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
                                            <p className="presents-muted">Брони скрыты. Посмотреть их можно на странице события.</p>
                                        </div>
                                    </div>
                                    <div className="presents-gift-bottom">
                                        <span className="presents-market">
                                            {gift.marketplace_url ? "🛍 Подключён" : "Маркетплейс не указан"}
                                        </span>
                                        <div className="presents-actions">
                                            <div className="presents-manage-actions">
                                                <button className="presents-button secondary" onClick={(event) => {
                                                    event.stopPropagation()
                                                    setEditingGift(gift)
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
                                <GiftEditForm
                                    gift={editingGift}
                                    onChange={setEditingGift}
                                    onSave={(imageId) => handleEdit(editingGift.id, {
                                        title: editingGift.title.trim(),
                                        price: Number(editingGift.price),
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
