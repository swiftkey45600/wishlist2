import { useEffect, useRef, useState } from "react"
import {
    addRecommendedGift,
    getRecommendations,
    isRecommendedGiftAdded,
    useRecommendationMocks
} from "../../../application/recommendationApplication"
import "./GiftRecommendations.css"
import { resolveImageUrl } from "../../../repositories/imageRepository"

function RecommendationImage({ url, emoji }) {
    const [failed, setFailed] = useState(false)
    return url && !failed
        ? <img src={resolveImageUrl(null, url)} alt="" onError={() => setFailed(true)} />
        : <span className="recommendation-placeholder" aria-hidden="true">{emoji || "🎁"}</span>
}

function GiftRecommendations({ eventId, gifts, onAdd }) {
    const [items, setItems] = useState([])
    const [isLoading, setIsLoading] = useState(true)
    const [loadError, setLoadError] = useState("")
    const [addError, setAddError] = useState("")
    const [pendingId, setPendingId] = useState(null)
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
                if (!cancelled) setItems(Array.isArray(data) ? data : [])
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
        if (submitting.current || !item || isRecommendedGiftAdded(item, gifts)) return
        submitting.current = true
        setPendingId(item.id)
        setAddError("")
        try {
            const gift = await addRecommendedGift(eventId, item)
            if (!gift?.id) throw new Error("Missing gift")
            if (!active.current) return
            onAdd?.(gift)
        } catch {
            if (active.current) setAddError("Не удалось добавить подарок. Попробуйте ещё раз.")
        } finally {
            submitting.current = false
            if (active.current) setPendingId(null)
        }
    }

    const available = items.filter(item => !isRecommendedGiftAdded(item, gifts))

    return (
        <section className="gift-recommendations" aria-labelledby="recommendations-heading">
            <h2 id="recommendations-heading">Может понравиться</h2>
            <p className="recommendations-note">{useRecommendationMocks
                ? "Примеры рекомендаций. Добавленные подарки сохраняются в вашем событии."
                : "Подарки из вашей истории и общего каталога с учётом тегов, цены и популярности."}</p>
            {isLoading && <p role="status">Подбираем подарки...</p>}
            {loadError && <div role="alert">
                <p>{loadError}</p>
                <button className="gift-secondary-button" onClick={() => setAttempt(value => value + 1)}>Повторить</button>
            </div>}
            {!isLoading && !loadError && (available.length ? (
                <div className="recommendations-grid">
                    {available.map(item => <article className="recommendation-card" key={item.id}>
                        <RecommendationImage key={item.picture_url || item.id} url={item.picture_url} emoji={item.emoji} />
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
        </section>
    )
}

export default GiftRecommendations
