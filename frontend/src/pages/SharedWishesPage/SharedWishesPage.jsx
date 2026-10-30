import GiftFundraising from "../../components/Gifts/GiftFundraising/GiftFundraising"
import { useEffect, useRef, useState } from "react"
import { Link, useParams } from "react-router-dom"
import { ArrowUpRight, Heart, LockKeyhole, ShieldCheck } from "lucide-react"
import { cancelSharedWish, getWishShare, reserveSharedWish, revokeWishShare } from "../../repositories/wishRepository"
import GiftImage from "../../components/Gifts/GiftImage/GiftImage"
import "./SharedWishesPage.css"

function safeUrl(value) {
    try {
        const url = new URL(value)
        return ["http:", "https:"].includes(url.protocol) ? url.href : ""
    } catch { return "" }
}

function ReservationDialog({ item, busy, error, onClose, onSubmit }) {
    const ref = useRef(null)
    const [name, setName] = useState("")
    const [secret, setSecret] = useState("")
    const cancelling = item.status === "reserved"
    useEffect(() => {
        const dialog = ref.current
        dialog.showModal()
        return () => dialog.close()
    }, [])
    return <dialog ref={ref} className="shared-wishes-modal" aria-labelledby="shared-reservation-title"
        onCancel={event => { event.preventDefault(); if (!busy) onClose() }}
        onClick={event => { if (event.target === event.currentTarget && !busy) onClose() }}>
        <form className="shared-wishes-dialog" onSubmit={event => { event.preventDefault(); onSubmit(cancelling ? { secret_word: secret } : { name, secret_word: secret }) }}>
            <LockKeyhole size={24} aria-hidden="true" />
            <h2 id="shared-reservation-title">{cancelling ? "Отменить бронь" : "Забронировать подарок"}</h2>
            <p>{item.title}</p>
            {!cancelling && <label>Ваше имя<input value={name} onChange={event => setName(event.target.value)} required maxLength={100} autoComplete="name" disabled={busy} /></label>}
            <label>Секретное слово<input type="password" value={secret} onChange={event => setSecret(event.target.value)} required autoComplete="off" aria-describedby="shared-secret-hint" disabled={busy} /></label>
            <p id="shared-secret-hint">{cancelling ? "Введите слово, которое указали при бронировании." : "Вход и почта не нужны. Запомните слово: оно понадобится для отмены брони. Не используйте пароль от аккаунта."}</p>
            {error && <p role="alert">{error}</p>}
            <div><button type="button" disabled={busy} onClick={onClose}>Закрыть</button><button type="submit" disabled={busy}>{busy ? "Сохраняем..." : cancelling ? "Отменить бронь" : "Забронировать"}</button></div>
        </form>
    </dialog>
}

export default function SharedWishesPage() {
    const { token } = useParams()
    const [data, setData] = useState(null)
    const [failed, setFailed] = useState(false)
    const [selected, setSelected] = useState(null)
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState("")
    const [revoking, setRevoking] = useState(false)
    const [revoked, setRevoked] = useState(false)
    const authenticated = Boolean(localStorage.getItem("accessToken"))

    useEffect(() => {
        let active = true
        async function refresh(initial = false) {
            try {
                const result = await getWishShare(token)
                if (active) { setData(result); setFailed(false) }
            } catch (requestError) {
                if (active && (initial || requestError.response?.status === 404)) { setData(null); setFailed(true) }
            }
        }
        refresh(true)
        const interval = setInterval(() => { if (!document.hidden) refresh() }, 15000)
        const handleFocus = () => refresh()
        window.addEventListener("focus", handleFocus)
        return () => { active = false; clearInterval(interval); window.removeEventListener("focus", handleFocus) }
    }, [token])

    async function changeReservation(item, credentials = {}) {
        if (busy) return
        if (credentials.secret_word && new TextEncoder().encode(credentials.secret_word).length > 72) {
            setError("Секретное слово слишком длинное. Выберите более короткое.")
            return
        }
        setBusy(true)
        setError("")
        try {
            if (item.status === "reserved") await cancelSharedWish(token, item.position, credentials)
            else await reserveSharedWish(token, item.position, credentials)
            setData(await getWishShare(token))
            setSelected(null)
        } catch (requestError) {
            const status = requestError.response?.status
            setError(status === 409 ? "Подарок уже забронирован или недоступен. Статус обновлён." : status === 403 ? "Не удалось отменить бронь. Проверьте секретное слово или аккаунт." : status === 422 ? "Введите имя и секретное слово." : status === 429 ? "Слишком много попыток. Попробуйте позже." : "Не удалось изменить бронь. Попробуйте ещё раз.")
            if (status === 409) {
                setSelected(null)
                try { setData(await getWishShare(token)) } catch { /* Keep the current view on a temporary network failure. */ }
            }
        } finally { setBusy(false) }
    }

    function handleAction(item) {
        setError("")
        if (authenticated) changeReservation(item)
        else setSelected(item)
    }

    async function revokeLink() {
        setBusy(true)
        try { await revokeWishShare(token); setRevoked(true); setData(null) }
        catch { setError("Не удалось закрыть доступ. Попробуйте ещё раз.") }
        finally { setBusy(false); setRevoking(false) }
    }

    return <main className="shared-wishes-page">
        <header className="shared-wishes-header">
            <span className="shared-wishes-brand"><Heart size={20} aria-hidden="true" /> Wishlist</span>
            <h1>Идеи для подарков</h1>
            <p>Выберите, чем порадовать. Забронируйте подарок, чтобы другие гости знали, что он занят.</p>
            <span className="shared-wishes-access"><ShieldCheck size={16} /> Бронь без регистрации</span>
            {!authenticated && <Link to={`/auth?next=${encodeURIComponent(`/wishes/shared/${token}`)}`}>Или войти в аккаунт <ArrowUpRight size={15} /></Link>}
        </header>
        {data?.is_owner && <aside className="shared-wishes-owner" role="note">
            <div><strong>Это ваш список</strong><p>Бронь от вас скрыта, чтобы сохранить сюрприз. Получатели ссылки увидят кнопку «Забронировать» без входа в аккаунт.</p></div>
            <button type="button" onClick={() => setRevoking(true)}>Закрыть доступ по ссылке</button>
            {revoking && <div><p>После этого ссылка перестанет открываться у всех получателей.</p><button type="button" onClick={() => setRevoking(false)}>Оставить ссылку</button><button type="button" disabled={busy} onClick={revokeLink}>Закрыть доступ</button></div>}
        </aside>}
        {data?.legacy && <p className="shared-wishes-notice">Ссылка создана в старой версии и не поддерживает бронь. Владельцу нужно заново поделиться выбранными подарками.</p>}
        {revoked && <p role="status">Доступ закрыт. Вы можете создать новую ссылку в разделе «Мои подарки».</p>}
        {failed && !revoked && <p role="alert">Не удалось открыть список. Возможно, владелец закрыл доступ по ссылке.</p>}
        {!data && !failed && !revoked && <p>Загружаем желания...</p>}
        {error && !selected && <p role="alert">{error}</p>}
        <div className="shared-wishes-grid">{data?.items.map(item => <article key={item.position}>
            <GiftImage gift={{ ...item, id: item.position }} className="shared-wishes-image" fallbackClassName="shared-wishes-image shared-wishes-placeholder" />
            <div className="shared-wishes-details"><h2>{item.title}</h2>
                {item.description && <p>{item.description}</p>}
                {item.price != null && <strong className="shared-wishes-price">{item.price.toLocaleString("ru-RU")} ₽</strong>}
                {safeUrl(item.marketplace_url) && <a href={safeUrl(item.marketplace_url)} target="_blank" rel="noopener noreferrer">Открыть товар <ArrowUpRight size={15} /></a>}
                {item.fundraising && <GiftFundraising
                    gift={item.fundraising}
                    publicToken={item.fundraising.public_token}
                    isOwner={data.is_owner}
                    hideContributionDetails={data.is_owner}
                    archived={item.status === "unavailable"}
                    onGiftChange={async () => setData(await getWishShare(token))}
                />}
                {item.status === "unavailable" && <p className="shared-wishes-notice">Подарок больше недоступен для бронирования.</p>}
                {item.status === "reserved" && <p className="shared-wishes-reserved">Забронирован{item.is_mine ? " вами" : ""}</p>}
                {!item.fundraising && item.status === "available" && <button type="button" disabled={busy} onClick={() => handleAction(item)}>Забронировать</button>}
                {item.status === "reserved" && (!authenticated || item.is_mine) && <button type="button" className="shared-wishes-cancel" disabled={busy} onClick={() => handleAction(item)}>Отменить бронь</button>}
            </div>
        </article>)}</div>
        {selected && <ReservationDialog item={selected} busy={busy} error={error} onClose={() => setSelected(null)} onSubmit={credentials => changeReservation(selected, credentials)} />}
    </main>
}
