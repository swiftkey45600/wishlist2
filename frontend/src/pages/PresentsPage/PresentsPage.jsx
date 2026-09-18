import { useEffect, useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"

import "./PresentsPage.css"
import Header from "../../components/Header/Header"
import Sidebar from "../../components/Sidebar/Sidebar"
import { getEvents } from "../../application/eventApplication"
import { getGiftsByEvent, deleteGift } from "../../application/giftApplication"

function getStatusClass(status) {
    return status === "reserved" ? "reserved" : status === "bought" ? "bought" : "available"
}

function getGiftCountLabel(count) {
    if (count % 10 === 1 && count % 100 !== 11) return "подарок"
    if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return "подарка"
    return "подарков"
}

function PresentsPage() {
    const navigate = useNavigate()
    const [events, setEvents] = useState([])
    const [gifts, setGifts] = useState([])
    const [search, setSearch] = useState("")
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState(null)

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

                setEvents(eventList)
                setGifts(giftGroups.flat())
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
        await deleteGift(giftId)
        setGifts((currentGifts) => currentGifts.filter((gift) => gift.id !== giftId))
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
                    {!isLoading && error && <p className="presents-status error-text">{error}</p>}
                    {!isLoading && !error && filteredGifts.length === 0 && (
                        <p className="presents-status">Подарки не найдены.</p>
                    )}

                    {!isLoading && !error && filteredGifts.length > 0 && (
                        <div className="presents-grid">
                            {filteredGifts.map((gift) => (
                                <article className="presents-gift-card" key={gift.id}>
                                    <div className="presents-gift-top">
                                        <img
                                            className="presents-pic"
                                            src={gift.picture_url || "https://via.placeholder.com/220x220?text=Gift"}
                                            alt={gift.title}
                                        />
                                        <div>
                                            <h3>{gift.title}</h3>
                                            <button
                                                className="presents-event-link"
                                                onClick={() => navigate(`/events/${gift.event.id}`)}
                                            >
                                                {gift.event.title}
                                            </button>
                                            <p className="presents-description">
                                                {gift.description || "Описание подарка пока не добавлено."}
                                            </p>
                                            <strong className="presents-price">{gift.price} ₽</strong>
                                            <span className={`presents-badge ${getStatusClass(gift.status)}`}>
                                                {gift.status}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="presents-gift-bottom">
                                        <span className="presents-market">
                                            {gift.marketplace_url ? "🛍 Маркетплейс подключён" : "Маркетплейс не указан"}
                                        </span>
                                        <div className="presents-actions">
                                            <button className="presents-button secondary" onClick={() => navigate(`/events/${gift.event.id}`)}>
                                                Открыть
                                            </button>

                                            <button className="presents-button secondary future" disabled>
                                                Изменить
                                            </button>

                                            <button className="presents-button danger" onClick={() => handleDelete(gift.id)}>
                                                Удалить
                                            </button>
                                        </div>
                                    </div>
                                </article>
                            ))}
                        </div>
                    )}
                </main>
            </div>
        </div>
    )
}

export default PresentsPage
