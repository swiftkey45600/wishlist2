import { useEffect, useRef, useState } from "react"
import { addContribution, cancelContribution, getContributions } from "../../../application/contributionApplication"
import "./GiftFundraising.css"

function validSecretWord(value) {
    return Boolean(value.trim()) && new TextEncoder().encode(value).length <= 72
}

function GiftFundraising({ gift, publicToken, isOwner, hideContributionDetails = false, onGiftChange }) {
    const [isOpen, setIsOpen] = useState(false)
    const [entries, setEntries] = useState([])
    const [isLoading, setIsLoading] = useState(false)
    const [hasLoaded, setHasLoaded] = useState(false)
    const [isBusy, setIsBusy] = useState(false)
    const [amount, setAmount] = useState("")
    const [name, setName] = useState("")
    const [secretWord, setSecretWord] = useState("")
    const [anonymous, setAnonymous] = useState(false)
    const [cancelling, setCancelling] = useState(null)
    const [cancelWord, setCancelWord] = useState("")
    const [error, setError] = useState("")
    const [notice, setNotice] = useState("")
    const active = useRef(false)
    const pending = useRef(false)
    const isAuthenticated = Boolean(localStorage.getItem("accessToken"))
    const total = gift.contribution_total || 0
    const goal = gift.contribution_goal
    const remaining = Math.max(0, goal - total)
    const canContribute = !isOwner && publicToken && remaining > 0 && gift.status === "available"
    const canViewContributions = !isOwner || !hideContributionDetails

    useEffect(() => {
        active.current = true
        return () => { active.current = false }
    }, [])

    async function refresh(includeGift = false) {
        setIsLoading(true)
        try {
            const [items] = await Promise.all([
                getContributions(gift.id, isOwner ? null : publicToken),
                includeGift ? onGiftChange?.() : undefined
            ])
            if (active.current) {
                setEntries(items)
                setHasLoaded(true)
            }
        } finally {
            if (active.current) setIsLoading(false)
        }
    }

    async function openContributions() {
        setError("")
        setIsOpen(true)
        try {
            await refresh()
        } catch (requestError) {
            if (active.current) setError(requestError.message)
        }
    }

    async function retryRefresh() {
        setError("")
        try {
            await refresh(true)
        } catch (requestError) {
            if (active.current) setError(requestError.message)
        }
    }

    async function submitContribution(event) {
        event.preventDefault()
        if (pending.current) return
        const value = Number(amount)
        setError("")
        setNotice("")
        if (!Number.isSafeInteger(value) || value <= 0 || value > remaining) {
            setError(`Введите сумму в целых рублях от 1 до ${remaining.toLocaleString("ru-RU")}.`)
            return
        }
        if (!isAuthenticated && (!name.trim() || !validSecretWord(secretWord))) {
            setError("Введите имя и непустое секретное слово. Если слово слишком длинное, сократите его.")
            return
        }
        pending.current = true
        setIsBusy(true)
        let saved = false
        try {
            await addContribution(publicToken, gift.id, {
                amount: value,
                is_anonymous: anonymous,
                ...(!isAuthenticated ? { name: name.trim(), secret_word: secretWord } : {})
            })
            saved = true
            if (!active.current) return
            setAmount("")
            setSecretWord("")
            setNotice("Взнос добавлен.")
            await refresh(true)
        } catch (requestError) {
            if (active.current) setError(saved
                ? "Взнос сохранён. Не удалось обновить данные — нажмите «Обновить сбор»."
                : requestError.message)
        } finally {
            pending.current = false
            if (active.current) setIsBusy(false)
        }
    }

    async function submitCancellation(event) {
        event.preventDefault()
        if (pending.current || !cancelling) return
        setError("")
        setNotice("")
        if (cancelling.requires_secret_word && !validSecretWord(cancelWord)) {
            setError("Введите секретное слово, указанное при взносе.")
            return
        }
        pending.current = true
        setIsBusy(true)
        let cancelled = false
        try {
            await cancelContribution(publicToken, gift.id, cancelling.id,
                cancelling.requires_secret_word ? cancelWord : undefined)
            cancelled = true
            if (!active.current) return
            setCancelling(null)
            setCancelWord("")
            setNotice("Взнос отменён.")
            await refresh(true)
        } catch (requestError) {
            if (active.current) setError(cancelled
                ? "Взнос отменён. Не удалось обновить данные — нажмите «Обновить сбор»."
                : requestError.message)
        } finally {
            pending.current = false
            if (active.current) setIsBusy(false)
        }
    }

    return (
        <section className="gift-fundraising" aria-label="Совместный сбор">
            <div className="fundraising-summary">
                <strong>Собрано {total.toLocaleString("ru-RU")} из {goal.toLocaleString("ru-RU")} ₽</strong>
                <span>{remaining > 0 ? `Осталось ${remaining.toLocaleString("ru-RU")} ₽` : "Цель достигнута"}</span>
            </div>
            <progress value={Math.min(total, goal)} max={goal} aria-label="Прогресс сбора" />
            <p className="fundraising-hint">Это учёт обещанных взносов: переводы и оплата через сайт не выполняются.</p>
            {(canContribute || canViewContributions) && <button type="button" className="gift-secondary-button" disabled={isLoading || isBusy}
                aria-expanded={isOpen}
                onClick={() => {
                    if (isOpen) {
                        setIsOpen(false)
                        setCancelling(null)
                        setCancelWord("")
                        setSecretWord("")
                    } else openContributions()
                }}>
                {isOpen ? "Скрыть взносы" : canContribute ? "Скинуться / посмотреть взносы" : "Посмотреть взносы"}
            </button>}
            {isOpen && canViewContributions && <div className="fundraising-details">
                <button type="button" className="gift-secondary-button" disabled={isBusy || isLoading} onClick={retryRefresh}>
                    Обновить сбор
                </button>
                {isLoading && <p role="status">Загружаем взносы...</p>}
                {!isLoading && hasLoaded && canViewContributions && entries.length === 0 && <p>Пока никто не внёс вклад.</p>}
                {canViewContributions && entries.length > 0 && <ul className="fundraising-entries">
                    {entries.map(entry => <li key={entry.id}>
                        <span>{entry.contributor_name || "Анонимно"} — {entry.amount.toLocaleString("ru-RU")} ₽</span>
                        {publicToken && entry.can_cancel && gift.status !== "bought" && <button type="button" className="gift-secondary-button"
                            disabled={isBusy || isLoading}
                            onClick={() => {
                                setCancelling(entry)
                                setCancelWord("")
                                setError("")
                                setNotice("")
                            }}>
                            {entry.requires_secret_word ? "Отменить по слову" : "Отменить свой взнос"}
                        </button>}
                    </li>)}
                </ul>}
                {cancelling && <form className="fundraising-form" onSubmit={submitCancellation}>
                    <strong>Отменить взнос {cancelling.amount.toLocaleString("ru-RU")} ₽?</strong>
                    {cancelling.requires_secret_word && <label>
                        Секретное слово для отмены
                        <input type="password" autoComplete="off" value={cancelWord}
                            disabled={isBusy} onChange={event => setCancelWord(event.target.value)} />
                    </label>}
                    <div className="fundraising-actions">
                        <button type="button" className="gift-secondary-button" disabled={isBusy}
                            onClick={() => { setCancelling(null); setCancelWord("") }}>Назад</button>
                        <button type="submit" className="gift-secondary-button" disabled={isBusy}>
                            Подтвердить отмену
                        </button>
                    </div>
                </form>}
                {canContribute && !cancelling && <form className="fundraising-form" onSubmit={submitContribution} noValidate>
                    <label>Сумма взноса, ₽
                        <input type="number" min="1" max={remaining} step="1" value={amount}
                            disabled={isBusy} onChange={event => setAmount(event.target.value)} />
                    </label>
                    {!isAuthenticated && <>
                        <label>Ваше имя
                            <input autoComplete="name" maxLength="100" value={name}
                                disabled={isBusy} onChange={event => setName(event.target.value)} />
                        </label>
                        <label>Секретное слово
                            <input type="password" autoComplete="off" value={secretWord}
                                disabled={isBusy} onChange={event => setSecretWord(event.target.value)} />
                        </label>
                        <p className="fundraising-hint">Запомните слово: оно понадобится для отмены взноса.</p>
                    </>}
                    <label className="fundraising-toggle">
                        <input type="checkbox" checked={anonymous} disabled={isBusy}
                            onChange={event => setAnonymous(event.target.checked)} />
                        Скрыть имя в списке
                    </label>
                    <button type="submit" className="add-gift-button" disabled={isBusy || isLoading}>
                        {isBusy ? "Сохраняем..." : "Внести вклад"}
                    </button>
                </form>}
                {notice && <p role="status">{notice}</p>}
                {error && <p className="gift-form-error" role="alert">{error}</p>}
            </div>}
        </section>
    )
}

export default GiftFundraising
