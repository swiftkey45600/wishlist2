import { useEffect, useRef, useState } from "react"
import { Link } from "react-router-dom"
import GiftImage from "../GiftImage/GiftImage"
import { addExistingGifts, getExistingGiftOptions } from "../../../repositories/giftRepository"
import "./ExistingGiftPicker.css"

function itemKey(item) { return `${item.kind}:${item.id}` }

export default function ExistingGiftPicker({ eventId, onAdded, onClose }) {
    const dialogRef = useRef(null)
    const [items, setItems] = useState([])
    const [selected, setSelected] = useState([])
    const [query, setQuery] = useState("")
    const [loading, setLoading] = useState(true)
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState("")
    const [attempt, setAttempt] = useState(0)

    useEffect(() => {
        const dialog = dialogRef.current
        dialog.showModal()
        return () => dialog.close()
    }, [])

    useEffect(() => {
        let active = true
        getExistingGiftOptions(eventId).then(result => {
            if (active) { setItems(result); setSelected(current => current.filter(key => result.some(item => itemKey(item) === key && !item.already_added && item.price != null))); setLoading(false); setError("") }
        }).catch(() => { if (active) { setError("Не удалось загрузить ваши подарки."); setLoading(false) } })
        return () => { active = false }
    }, [eventId, attempt])

    async function submit(event) {
        event.preventDefault()
        if (busy || loading || !selected.length) return
        setBusy(true)
        setError("")
        try {
            const choices = items.filter(item => selected.includes(itemKey(item))).map(({ kind, id }) => ({ kind, id }))
            onAdded(await addExistingGifts(eventId, choices))
        } catch (requestError) {
            const status = requestError.response?.status
            setError(status === 409 ? "Событие уже в архиве. Добавьте подарки в активное событие." : status === 404 ? "Один из подарков изменился или был удалён. Обновите список." : "Не удалось добавить подарки. Выбранные вещи сохранены — попробуйте ещё раз.")
        } finally { setBusy(false) }
    }

    const search = query.trim().toLocaleLowerCase("ru-RU")
    const visibleItems = items.filter(item => !search || [item.title, ...item.tags].some(value => value.toLocaleLowerCase("ru-RU").includes(search)))
    return <dialog ref={dialogRef} className="existing-gift-dialog" aria-labelledby="existing-gift-title"
        onCancel={event => { event.preventDefault(); if (!busy) onClose() }}
        onClick={event => { if (event.target === event.currentTarget && !busy) onClose() }}>
        <form onSubmit={submit}>
            <header><h2 id="existing-gift-title">Из моих подарков</h2><p>Выберите желания или подарки из других событий. В это событие добавятся копии, без прежних броней.</p></header>
            <input className="existing-gift-search" type="search" placeholder="Поиск по названию или тегу" aria-label="Найти существующий подарок" value={query} onChange={event => setQuery(event.target.value)} />
            {loading && <p role="status">Загружаем подарки...</p>}
            {!loading && items.length === 0 && !error && <p>Пока нет подарков для добавления. Создайте желание в разделе <Link to="/presents">«Мои подарки»</Link>.</p>}
            {!loading && items.length > 0 && !visibleItems.length && <p>По вашему запросу ничего не найдено.</p>}
            <div className="existing-gift-list">{visibleItems.map(item => {
                const disabled = item.already_added || item.price == null
                const key = itemKey(item)
                return <label className={`existing-gift-option${disabled ? " existing-gift-option--disabled" : ""}`} key={key}>
                    <input type="checkbox" aria-label={`Добавить «${item.title}»${item.source_title ? ` из «${item.source_title}»` : ""}`} checked={selected.includes(key)} disabled={disabled || busy || (selected.length >= 50 && !selected.includes(key))}
                        onChange={event => setSelected(current => event.target.checked ? [...current, key] : current.filter(value => value !== key))} />
                    <GiftImage gift={item} className="existing-gift-image" fallbackClassName="existing-gift-image existing-gift-placeholder" />
                    <span className="existing-gift-description"><strong>{item.title}</strong><small>{item.source_title ? `Из события «${item.source_title}»` : "Из моих подарков"}</small><small>{item.already_added ? "Уже в событии" : item.price == null ? "Сначала укажите цену в «Мои подарки»" : `${item.price.toLocaleString("ru-RU")} ₽`}</small>
                    {!!item.tags.length && <small>{item.tags.join(" · ")}</small>}</span>
                </label>
            })}</div>
            {error && <div role="alert"><p>{error}</p><button className="existing-gift-reload" type="button" disabled={busy} onClick={() => { setLoading(true); setAttempt(value => value + 1) }}>Обновить список</button></div>}
            <footer><button type="button" disabled={busy} onClick={onClose}>Отмена</button><button type="submit" disabled={busy || loading || !selected.length}>{busy ? "Добавляем..." : `Добавить выбранные (${selected.length})`}</button></footer>
        </form>
    </dialog>
}
