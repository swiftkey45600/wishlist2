import { useEffect, useRef, useState } from "react"
import {
    addRecommendedGift,
    getRecommendations,
    isRecommendedGiftAdded,
    useRecommendationMocks
} from "../../../application/recommendationApplication"
import "./GiftRecommendations.css"

function RecommendationImage({ url }) {
    const [failed, setFailed] = useState(false)
    return url && !failed
        ? <img src={url} alt="" onError={() => setFailed(true)} />
        : <span className="recommendation-placeholder" aria-hidden="true">🎁</span>
}

function GiftRecommendations({ eventId, gifts, onAdd }) {
    const [items, setItems] = useState([])
    const [isLoading, setIsLoading] = useState(true)
    const [loadError, setLoadError] = useState("")
    const [addError, setAddError] = useState("")
    const [pendingId, setPendingId] = useState(null)
    const [notice, setNotice] = useState("")
    const [attempt, setAttempt] = useState(0)
    const submitting = useRef(false)
    const active = useRef(false)

    useEffect(() => {
        active.current = true
        return () => { active.current = false }
    }, [])

    useEffect(() => {
        let cancelled = false
        async function load() {
            setIsLoading(true)
            setLoadError("")
            try {
                const data = await getRecommendations(eventId)
                if (!cancelled) setItems(data)
            } catch {
                if (!cancelled) setLoadError("Не удалось загрузить рекомендации.")
            } finally {
                if (!cancelled) setIsLoading(false)
            }
        }
        load()
        return () => { cancelled = true }
    }, [eventId, attempt])

    async function handleAdd(item) {
        if (submitting.current || isRecommendedGiftAdded(item, gifts)) return
        submitting.current = true
        setPendingId(item.id)
        setAddError("")
        setNotice("")
        try {
            const gift = await addRecommendedGift(eventId, item)
            if (!gift?.id) throw new Error("Missing gift")
            if (!active.current) return
            onAdd(gift)
            setNotice(`«${gift.title}» добавлен в событие`)
        } catch {
            if (active.current) setAddError("Не удалось добавить подарок. Попробуйте ещё раз.")
        } finally {
            submitting.current = false
            if (active.current) setPendingId(null)
        }
    }

    // До согласования ручки с бэкендом блок доступен только с dev-заглушкой.
    if (!useRecommendationMocks) return null
    const available = items.filter(item => !isRecommendedGiftAdded(item, gifts))

    return (
        <section className="gift-recommendations" aria-labelledby="recommendations-heading">
            <h2 id="recommendations-heading">Может понравиться</h2>
            <p className="recommendations-note">Примеры рекомендаций. Добавленные подарки сохраняются в вашем событии.</p>
            {isLoading && <p role="status">Подбираем подарки...</p>}
            {loadError && <div role="alert">
                <p>{loadError}</p>
                <button className="gift-secondary-button" onClick={() => setAttempt(value => value + 1)}>Повторить</button>
            </div>}
            {!isLoading && !loadError && (available.length ? (
                <div className="recommendations-grid">
                    {available.map(item => <article className="recommendation-card" key={item.id}>
                        <RecommendationImage key={item.picture_url || "placeholder"} url={item.picture_url} />
                        <h3>{item.title}</h3>
                        <p>{item.description}</p>
                        <strong>{item.price == null ? "Цена не указана" : `${item.price.toLocaleString("ru-RU")} ₽`}</strong>
                        <button className="add-gift-button" disabled={pendingId !== null} onClick={() => handleAdd(item)}>
                            {pendingId === item.id ? "Добавляем..." : "Добавить в событие"}
                        </button>
                    </article>)}
                </div>
            ) : <p>Пока нет новых рекомендаций.</p>)}
            {addError && <p className="gift-form-error" role="alert">{addError}</p>}
            <p role="status">{notice}</p>
        </section>
    )
}

export default GiftRecommendations
