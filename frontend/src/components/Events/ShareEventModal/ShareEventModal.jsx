import { useState } from "react"
import "./ShareEventModal.css"

function ShareEventModal({ event, shareLink, onClose }) {
    const [message, setMessage] = useState("")

    async function handleCopy() {
        try {
            if (navigator.clipboard?.writeText) {
                await navigator.clipboard.writeText(shareLink)
            } else {
                const input = document.createElement("textarea")
                input.value = shareLink
                input.setAttribute("readonly", "")
                input.style.position = "fixed"
                input.style.top = "-9999px"
                document.body.appendChild(input)
                input.select()
                const copied = document.execCommand("copy")
                document.body.removeChild(input)
                if (!copied) throw new Error("Браузер не разрешил скопировать ссылку")
            }

            setMessage("Ссылка скопирована")
        } catch (error) {
            console.error("Не удалось скопировать ссылку", error)
            setMessage("Не удалось скопировать ссылку. Скопируйте её вручную.")
        }
    }

    const telegramUrl = new URL("https://t.me/share/url")
    telegramUrl.searchParams.set("url", shareLink)
    telegramUrl.searchParams.set("text", `Приглашаю посмотреть событие «${event.title}»`)

    return (
        <div
            className="share-event-overlay"
            onClick={clickEvent => {
                if (clickEvent.target === clickEvent.currentTarget) onClose()
            }}
        >
            <section
                className="share-event-dialog"
                role="dialog"
                aria-modal="true"
                aria-labelledby="share-event-title"
            >
                <button className="share-event-close" type="button" onClick={onClose} aria-label="Закрыть">×</button>
                <h2 id="share-event-title">Поделиться событием</h2>
                <p className="share-event-description">{event.title}</p>

                <div className="share-event-qr-placeholder" role="img" aria-label="QR-код пока недоступен">
                    <span>QR-код появится здесь</span>
                </div>

                <label className="share-event-link">
                    Ссылка на событие
                    <input readOnly value={shareLink} onFocus={inputEvent => inputEvent.target.select()} />
                </label>
                <div className="share-event-actions">
                    <button className="share-event-copy" type="button" onClick={handleCopy}>
                        Копировать ссылку
                    </button>
                    <a className="share-event-telegram" href={telegramUrl.toString()} target="_blank" rel="noopener noreferrer">
                        Отправить в Telegram
                    </a>
                </div>
                {message && <p className="share-event-message" role="status">{message}</p>}
            </section>
        </div>
    )
}

export default ShareEventModal
