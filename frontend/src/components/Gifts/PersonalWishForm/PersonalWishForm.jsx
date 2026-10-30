import { useState } from "react"
import { createPortal } from "react-dom"
import { uploadImageFile } from "../../../application/imageApplication"
import { createWish, editWish } from "../../../repositories/wishRepository"
import "./PersonalWishForm.css"

function PersonalWishForm({ wish, onSaved, onCancel }) {
    const [title, setTitle] = useState(wish?.title || "")
    const [price, setPrice] = useState(wish?.price ?? "")
    const [priority, setPriority] = useState(wish?.priority || "normal")
    const [description, setDescription] = useState(wish?.description || "")
    const [marketplaceUrl, setMarketplaceUrl] = useState(wish?.marketplace_url || "")
    const [pictureUrl, setPictureUrl] = useState(wish?.picture_url || "")
    const [tags, setTags] = useState((wish?.tags || []).map(tag => typeof tag === "string" ? tag : tag.name).join(", "))
    const [file, setFile] = useState(null)
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState("")

    async function submit(event) {
        event.preventDefault()
        const amount = price === "" ? null : Number(price)
        if (!title.trim() || (amount !== null && (!Number.isSafeInteger(amount) || amount <= 0))) {
            setError("Введите название и, если указываете цену, положительное число в рублях.")
            return
        }
        setBusy(true)
        setError("")
        try {
            let imageId = wish?.image_id || null
            if (file) {
                const image = await uploadImageFile(file)
                if (!image?.id) { setError("Не удалось загрузить изображение. Выберите другой файл или уберите его."); return }
                imageId = image.id
            } else if (pictureUrl.trim() !== (wish?.picture_url || "")) imageId = null
            const data = { title: title.trim(), price: amount, description: description.trim() || null,
                marketplace_url: marketplaceUrl.trim() || null, picture_url: imageId ? null : pictureUrl.trim() || null,
                image_id: imageId, priority, tags: tags.split(",").map(tag => tag.trim()).filter(Boolean) }
            const result = wish ? await editWish(wish.id, data) : await createWish(data)
            onSaved(result)
        } catch { setError("Не удалось сохранить желание. Проверьте данные и попробуйте ещё раз.") }
        finally { setBusy(false) }
    }

    return createPortal(<div className="personal-wish-overlay" onClick={event => { if (event.target === event.currentTarget && !busy) onCancel() }}>
        <form className="personal-wish-form" onSubmit={submit}>
            <h2>{wish ? "Изменить желание" : "Новое желание"}</h2>
            <p>Сохраните идею сейчас, а в событие добавьте позже.</p>
            <label>Название<input value={title} onChange={event => setTitle(event.target.value)} autoFocus required maxLength={200} /></label>
            <label>Цена, ₽ <span>необязательно</span><input type="number" min="1" step="1" value={price} onChange={event => setPrice(event.target.value)} /></label>
            <label>Насколько хочется<select value={priority} onChange={event => setPriority(event.target.value)}><option value="high">Очень хочу</option><option value="normal">Хочу</option><option value="low">Не срочно</option></select></label>
            <label>Описание<textarea value={description} onChange={event => setDescription(event.target.value)} /></label>
            <label>Ссылка на товар<input type="url" value={marketplaceUrl} onChange={event => setMarketplaceUrl(event.target.value)} placeholder="https://..." /></label>
            <label>Ссылка на изображение<input type="url" value={pictureUrl} onChange={event => setPictureUrl(event.target.value)} placeholder="https://..." /></label>
            <label>Или загрузите изображение<input type="file" accept="image/jpeg,image/png,image/webp,image/gif" onChange={event => setFile(event.target.files?.[0] || null)} /></label>
            {file && <button className="personal-clear" type="button" onClick={() => setFile(null)}>Убрать выбранный файл</button>}
            <label>Теги через запятую<input value={tags} onChange={event => setTags(event.target.value)} placeholder="Книги, Хобби" /></label>
            {error && <p className="personal-error" role="alert">{error}</p>}
            <div className="personal-actions"><button type="button" className="presents-button secondary" disabled={busy} onClick={onCancel}>Отмена</button><button className="presents-button primary" disabled={busy}>{busy ? "Сохраняем..." : "Сохранить"}</button></div>
        </form>
    </div>, document.body)
}
export default PersonalWishForm
