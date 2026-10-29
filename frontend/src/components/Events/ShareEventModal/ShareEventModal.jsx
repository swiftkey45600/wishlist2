import { useEffect, useRef, useState } from "react"
import QRCode from "qrcode"
import { Copy, Download, Link2, Send, Share2, X } from "lucide-react"
import "./ShareEventModal.css"

function ShareEventModal({ event, shareLink, onClose, isWishShare = false }) {
    const [message, setMessage] = useState("")
    const [qrImage, setQrImage] = useState("")
    const [qrError, setQrError] = useState(false)
    const linkRef = useRef(null)

    useEffect(() => {
        let cancelled = false
        QRCode.toDataURL(shareLink, { width: 600, margin: 3, errorCorrectionLevel: "M", color: { dark: "#38265e", light: "#ffffff" } })
            .then(image => { if (!cancelled) setQrImage(image) })
            .catch(() => { if (!cancelled) setQrError(true) })
        return () => { cancelled = true }
    }, [shareLink])

    async function handleCopy() {
        try {
            if (!navigator.clipboard?.writeText) throw new Error("Clipboard unavailable")
            await navigator.clipboard.writeText(shareLink)
            setMessage("Ссылка скопирована")
        } catch {
            linkRef.current?.focus()
            linkRef.current?.select()
            try {
                if (document.execCommand("copy")) {
                    setMessage("Ссылка скопирована")
                    return
                }
            } catch { /* The selected link can still be copied manually. */ }
            setMessage("Выделили ссылку — скопируйте её сочетанием ⌘C или Ctrl+C")
        }
    }

    async function handleCopyQr() {
        try {
            if (!qrImage || !navigator.clipboard?.write || typeof ClipboardItem === "undefined") throw new Error("Clipboard unavailable")
            const png = fetch(qrImage).then(response => response.blob())
            await navigator.clipboard.write([new ClipboardItem({ "image/png": png })])
            setMessage("QR-код скопирован")
        } catch {
            setMessage("Не удалось скопировать QR-код. Скачайте его кнопкой ниже.")
        }
    }

    async function handleShare() {
        try {
            await navigator.share({ title: event.title, text: isWishShare ? "Делюсь идеями подарков" : `Приглашаю посмотреть событие «${event.title}»`, url: shareLink })
        } catch (error) {
            if (error.name !== "AbortError") setMessage("Не удалось открыть отправку. Скопируйте ссылку или отправьте её в Telegram.")
        }
    }

    const telegramUrl = new URL("https://t.me/share/url")
    telegramUrl.searchParams.set("url", shareLink)
    telegramUrl.searchParams.set("text", isWishShare ? "Делюсь идеями подарков" : `Приглашаю посмотреть событие «${event.title}»`)

    return (
        <div className="share-event-overlay" onClick={clickEvent => { if (clickEvent.target === clickEvent.currentTarget) onClose() }}>
            <section className="share-event-dialog" role="dialog" aria-modal="true" aria-labelledby="share-event-title">
                <button className="share-event-close" type="button" onClick={onClose} aria-label="Закрыть"><X size={20} /></button>
                <span className="share-event-eyebrow"><Share2 size={14} /> ДЕЛИТЬСЯ ЛЕГКО</span>
                <h2 id="share-event-title">Пусть знают, о чём вы мечтаете</h2>
                <p className="share-event-description">{isWishShare ? "Отправьте друзьям выбранные подарки" : `Отправьте друзьям вишлист «${event.title}»`}</p>
                <div className="share-event-qr-wrap">
                    {qrImage ? <img src={qrImage} alt="QR-код для перехода к событию" className="share-event-qr" /> :
                        <div className="share-event-qr-loading" role="status">{qrError ? "Не удалось создать QR-код" : "Создаём QR-код…"}</div>}
                    <p>{isWishShare ? "Любой, у кого есть ссылка, увидит выбранные подарки и сможет их забронировать." : "Наведите камеру, чтобы открыть список"}</p>
                    <div className="share-event-qr-actions">
                        <button type="button" onClick={handleCopyQr} disabled={!qrImage}><Copy size={15} /> Копировать QR</button>
                        <a href={qrImage || undefined} download="wishlist-qr.png" aria-disabled={!qrImage} onClick={e => { if (!qrImage) e.preventDefault() }}><Download size={15} /> Скачать QR</a>
                    </div>
                </div>
                <label className="share-event-link">
                    <span>{isWishShare ? "Ссылка на подарки" : "Ссылка на событие"}</span>
                    <span className="share-event-link-row"><Link2 size={17} /><input ref={linkRef} readOnly value={shareLink} onFocus={inputEvent => inputEvent.target.select()} /><button type="button" onClick={handleCopy} aria-label="Копировать ссылку"><Copy size={17} /></button></span>
                </label>
                <div className="share-event-actions">
                    <button className="share-event-copy" type="button" onClick={handleCopy}><Copy size={16} /> Копировать ссылку</button>
                    <a className="share-event-telegram" href={telegramUrl.toString()} target="_blank" rel="noopener noreferrer"><Send size={16} /> Telegram</a>
                    {typeof navigator.share === "function" && <button className="share-event-native" type="button" onClick={handleShare}><Share2 size={16} /> Ещё</button>}
                </div>
                {message && <p className="share-event-message" role="status">{message}</p>}
            </section>
        </div>
    )
}

export default ShareEventModal
