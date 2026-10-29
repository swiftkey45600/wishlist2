import SegmentedControl from "../../components/SegmentedControl/SegmentedControl"
import { useEffect, useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"

import "./PresentsPage.css"
import Header from "../../components/Header/Header"
import Sidebar from "../../components/Sidebar/Sidebar"
import { getEvents, createEvent } from "../../application/eventApplication"
import CreateEventForm from "../../components/Events/CreateEventForm/CreateEventForm"
import ShareEventModal from "../../components/Events/ShareEventModal/ShareEventModal"
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
import { carryGift, setGiftReceived, fetchGift } from "../../repositories/giftRepository"
import { getWishes, removeWish, receiveWish, addWishToEvent, createWishShare } from "../../repositories/wishRepository"
import PersonalWishForm from "../../components/Gifts/PersonalWishForm/PersonalWishForm"

function productLink(value) {
    try {
        const url = new URL(value)
        return ["http:", "https:"].includes(url.protocol) ? url.href : ""
    } catch { return "" }
}

function getGiftCountLabel(count) {
    if (count % 10 === 1 && count % 100 !== 11) return "подарок"
    if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return "подарка"
    return "подарков"
}

function personalGift(wish) {
    return { ...wish, isPersonal: true, event: null,
        tags: (wish.tags || []).map((name, index) => ({ id: `personal-${index}`, name })) }
}

function PresentsPage() {
    const navigate = useNavigate()
    const [gifts, setGifts] = useState([])
    const [events, setEvents] = useState([])
    const [personalForm, setPersonalForm] = useState(null)
    const [notice, setNotice] = useState("")
    const [pendingEventGift, setPendingEventGift] = useState(null)
    const [selectedShares, setSelectedShares] = useState([])
    const [shareLink, setShareLink] = useState("")
    const [shareBusy, setShareBusy] = useState(false)
    const [giftTab, setGiftTab] = useState("active")
    const [busyGift, setBusyGift] = useState(null)
    const [search, setSearch] = useState("")
    const [selectedTag, setSelectedTag] = useState("")
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
                const [loadedEvents, personalWishes] = await Promise.all([getEvents(), getWishes()])
                const eventList = Array.isArray(loadedEvents) ? loadedEvents : []
                setEvents(eventList)
                const giftGroups = await Promise.all(
                    eventList.map(async (event) => {
                        const eventGifts = await getGiftsByEvent(event.id)
                        return (Array.isArray(eventGifts) ? eventGifts : []).map((gift) => ({
                            ...gift,
                            event,
                        }))
                    })
                )

                setGifts([...personalWishes.map(personalGift), ...applySavedGiftPriorities(giftGroups.flat())])
            } catch (loadError) {
                console.error(loadError)
                setError("Не удалось загрузить подарки")
            } finally {
                setIsLoading(false)
            }
        }

        loadGifts()
    }, [])

    const giftTags = useMemo(() => {
        const names = new Map()
        gifts.forEach(gift => (gift.tags || []).forEach(tag => {
            const key = tag.name.trim().toLocaleLowerCase("ru-RU")
            if (key && !names.has(key)) names.set(key, tag.name.trim())
        }))
        return [...names].sort((a, b) => a[1].localeCompare(b[1], "ru"))
    }, [gifts])

    const filteredGifts = useMemo(() => {
        const query = search.trim().toLowerCase()

        return gifts.filter((gift) => {
            const matchesSearch = !query || gift.title?.toLowerCase().includes(query)
            const matchesTag = !selectedTag || gift.tags?.some(tag => tag.name.trim().toLocaleLowerCase("ru-RU") === selectedTag)
            const matchesTab = giftTab === "received" ? gift.received : !gift.received && !gift.carried_forward
            return matchesSearch && matchesTag && matchesTab
        })
    }, [gifts, search, selectedTag, giftTab])

    async function handleReceived(gift, received) {
        setBusyGift(gift.id)
        setError(null)
        try {
            const updated = gift.isPersonal ? personalGift(await receiveWish(gift.id, received)) : await setGiftReceived(gift.id, received)
            setGifts(current => current.map(item => item.id === gift.id && Boolean(item.isPersonal) === Boolean(gift.isPersonal) ? { ...item, ...updated, event: item.event } : item))
        } catch { setError("Не удалось изменить отметку. Попробуйте ещё раз.") }
        finally { setBusyGift(null) }
    }

    async function handleCarry(gift, eventId, createdEvent = null) {
        if (!eventId) return false
        if (eventId === "create") {
            if (gift.price == null) { setError("Перед добавлением в событие укажите цену желания."); return false }
            setPendingEventGift(gift)
            return false
        }
        setBusyGift(gift.id)
        setError(null)
        try {
            const destination = createdEvent || events.find(event => event.id === Number(eventId))
            if (gift.isPersonal) {
                const created = await addWishToEvent(gift.id, Number(eventId))
                const copied = await fetchGift(created.gift_id)
                setGifts(current => [...current, { ...copied, event: destination }])
                setNotice(`Желание добавлено в событие «${destination.title}».`)
            } else {
                const copied = await carryGift(gift.id, Number(eventId))
                setGifts(current => [...current.map(item => item.id === gift.id && !item.isPersonal ? { ...item, carried_forward: true } : item), { ...copied, event: destination }])
                setNotice(`Подарок перенесён в событие «${destination.title}».`)
            }
            return true
        } catch (requestError) { setError(requestError.response?.data?.detail === "Set a price before adding to an event" ? "Перед добавлением в событие укажите цену желания." : "Не удалось добавить подарок. Обновите страницу и попробуйте ещё раз."); return false }
        finally { setBusyGift(null) }
    }

    function shareKey(gift) { return `${gift.isPersonal ? "wish" : "gift"}:${gift.id}` }

    const selectedGiftItems = gifts.filter(gift => selectedShares.includes(shareKey(gift)) && !gift.received && !gift.carried_forward)

    async function handleShare(items) {
        if (!items.length || shareBusy) return
        setShareBusy(true)
        setError(null)
        try {
            const response = await createWishShare(items.map(item => ({ kind: item.isPersonal ? "wish" : "gift", id: item.id })))
            setShareLink(`${window.location.origin}/wishes/shared/${response.token}`)
        } catch { setError("Не удалось создать ссылку. Попробуйте ещё раз.") }
        finally { setShareBusy(false) }
    }

    async function handleDelete(gift) {
        if (gift.isPersonal) {
            try { await removeWish(gift.id); setGifts(current => current.filter(item => !(item.isPersonal && item.id === gift.id))) }
            catch { setError("Не удалось удалить желание. Попробуйте ещё раз.") }
            return
        }
        const giftId = gift.id
        if (!await deleteGift(giftId)) {
            setError("Не удалось удалить подарок. Попробуйте ещё раз.")
            return
        }
        removeSavedGiftPriority(giftId)
        setError(null)
        setGifts((currentGifts) => currentGifts.filter((item) => item.isPersonal || item.id !== giftId))
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
                            <div className="presents-muted">Ваши желания и подарки — с событием и без</div>
                        </div>

                        <button className="presents-button primary" onClick={() => setPersonalForm({})}>
                            ＋ Добавить желание
                        </button>
                    </div>

                    <SegmentedControl label="Разделы подарков" value={giftTab} onChange={setGiftTab}
                        options={[{ value: "active", label: "Мои желания" }, { value: "received", label: "Подаренные" }]} />
                    <div className="presents-toolbar">
                        <div className="presents-search">
                            <span aria-hidden="true">⌕</span>

                            <input
                                value={search}
                                onChange={(event) => setSearch(event.target.value)}
                                placeholder="Поиск по названию подарка..."
                            />
                        </div>
                        <select aria-label="Фильтр по тегу" value={selectedTag} onChange={event => setSelectedTag(event.target.value)}>
                            <option value="">Все теги</option>
                            {giftTags.map(([key, name]) => <option key={key} value={key}>{name}</option>)}
                        </select>
                    </div>

                    {giftTab === "active" && <div className="presents-share-list"><span>Отметьте подарки, чтобы поделиться списком</span><button type="button" className="presents-button secondary" disabled={!selectedGiftItems.length || shareBusy} onClick={() => handleShare(selectedGiftItems)}>Поделиться выбранным ({selectedGiftItems.length})</button></div>}
                    <div className="presents-section-title">
                        <h2>{giftTab === "received" ? "Подаренные" : "Мои желания"}</h2>
                        <span>{filteredGifts.length} {getGiftCountLabel(filteredGifts.length)}</span>
                    </div>

                    {isLoading && <p className="presents-status">Загружаем подарки...</p>}
                    {error && <p className="presents-status error-text" role="alert">{error}</p>}
                    {notice && <p className="presents-status" role="status">{notice}</p>}
                    {!isLoading && !error && filteredGifts.length === 0 && (
                        <p className="presents-status">{giftTab === "received" ? "Подаренных подарков пока нет." : "Подарки не найдены."}</p>
                    )}

                    {!isLoading && filteredGifts.length > 0 && (
                        <div className="presents-grid">
                            {filteredGifts.map((gift) => (
                                <article
                                    className="presents-gift-card"
                                    key={`${gift.isPersonal ? "wish" : "gift"}-${gift.id}`}
                                    onClick={() => { if (gift.event) navigate(`/events/${gift.event.id}`) }}
                                >
                                    <div className="presents-gift-top">
                                        {giftTab === "active" && <label className="presents-select" onClick={event => event.stopPropagation()}><input type="checkbox" checked={selectedShares.includes(shareKey(gift))} onChange={event => setSelectedShares(current => event.target.checked ? [...current, shareKey(gift)] : current.filter(key => key !== shareKey(gift)))} aria-label={`Выбрать «${gift.title}» для списка`} /></label>}
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
                                            {gift.event ? <button className="presents-event-link" onClick={(event) => { event.stopPropagation(); navigate(`/events/${gift.event.id}`) }}>{gift.event.title}</button> : null}
                                            <p className="presents-description">
                                                {gift.description || "Описание подарка пока не добавлено."}
                                            </p>
                                            <strong className="presents-price">{gift.price == null ? "Цена не указана" : `${gift.price} ₽`}</strong>
                                        </div>
                                    </div>
                                    <div className="presents-gift-bottom">
                                        {giftTab === "active" && <button className="presents-share-one" type="button" disabled={shareBusy} onClick={event => { event.stopPropagation(); handleShare([gift]) }}>Поделиться ↗</button>}
                                        {productLink(gift.marketplace_url) && <a className="presents-market" href={productLink(gift.marketplace_url)} target="_blank" rel="noopener noreferrer" onClick={event => event.stopPropagation()}>Открыть товар ↗</a>}
                                        <div className="presents-actions">
                                            <div className="presents-manage-actions">
                                                <button className="presents-button secondary" disabled={busyGift === gift.id} onClick={(event) => {
                                                    event.stopPropagation()
                                                    handleReceived(gift, !gift.received)
                                                }}>{gift.received ? "Вернуть в желания" : "Мне подарили"}</button>
                                                {!gift.received && (gift.isPersonal || gift.event.status === "archived") && <select
                                                    aria-label={`${gift.isPersonal ? "Добавить" : "Перенести"} «${gift.title}» в событие`} value="" disabled={busyGift === gift.id}
                                                    onClick={event => event.stopPropagation()}
                                                    onChange={event => handleCarry(gift, event.target.value)}>
                                                    <option value="">{gift.isPersonal ? "Добавить в событие…" : "Перенести в событие…"}</option>
                                                    <option value="create">＋ Создать событие</option>
                                                    {events.filter(event => event.status !== "archived").map(event => <option key={event.id} value={event.id}>{event.title}</option>)}
                                                </select>}
                                                <button className="presents-button secondary" onClick={(event) => {
                                                    event.stopPropagation()
                                                    if (gift.isPersonal) setPersonalForm(gift)
                                                    else setEditingGift({ ...gift, tag_ids: gift.tags?.map(tag => tag.id) || [] })
                                                }}>
                                                    Изменить
                                                </button>

                                                <button className="presents-button danger" onClick={(event) => {
                                                    event.stopPropagation()
                                                    handleDelete(gift)
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

                    {shareLink && <ShareEventModal event={{ title: "Подарки" }} isWishShare shareLink={shareLink} onClose={() => setShareLink("")} />}
                    {pendingEventGift && <div className="personal-wish-overlay"><div className="presents-create-event-dialog"><CreateEventForm onCancel={() => setPendingEventGift(null)} onCreateEvent={async data => {
                        const created = await createEvent(data)
                        if (!created) return false
                        setEvents(current => [...current, created])
                        const added = await handleCarry(pendingEventGift, created.id, created)
                        setPendingEventGift(null)
                        if (!added) setError("Событие создано, но подарок не добавлен. Попробуйте ещё раз.")
                        return true
                    }} /></div></div>}
                    {personalForm && <PersonalWishForm wish={personalForm.id ? personalForm : null} onCancel={() => setPersonalForm(null)} onSaved={wish => {
                        const item = personalGift(wish)
                        setGifts(current => [item, ...current.filter(existing => !(existing.isPersonal && existing.id === item.id))])
                        setPersonalForm(null)
                        setGiftTab(item.received ? "received" : "active")
                    }} />}
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
                                    onSave={(imageId, tagIds) => handleEdit(editingGift.id, {
                                        title: editingGift.title.trim(),
                                        price: Number(editingGift.price),
                                        contribution_goal: parseContributionGoal(editingGift.contribution_goal, editingGift.contribution_total),
                                        tag_ids: tagIds,
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
