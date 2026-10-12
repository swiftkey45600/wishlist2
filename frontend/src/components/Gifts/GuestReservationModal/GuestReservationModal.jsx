import { useEffect, useRef, useState } from "react"
import { Link } from "react-router-dom"
import {
    changeGuestReservation,
    useGuestReservationMocks
} from "../../../application/guestReservationApplication"
import "./GuestReservationModal.css"

function GuestReservationModal({ token, gift, onSuccess, onCancel }) {
    const dialogRef = useRef(null)
    const [name, setName] = useState("")
    const [secretWord, setSecretWord] = useState("")
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [error, setError] = useState("")
    const isCancelling = gift.status === "reserved"

    useEffect(() => {
        const dialog = dialogRef.current
        dialog.showModal()
        return () => dialog.close()
    }, [])

    async function handleSubmit(event) {
        event.preventDefault()
        if (isSubmitting) return
        if (!secretWord.trim() || (!isCancelling && !name.trim())) {
            setError(isCancelling ? "Введите секретное слово" : "Введите имя и секретное слово")
            return
        }

        setError("")
        setIsSubmitting(true)
        try {
            const updatedGift = await changeGuestReservation(token, gift, { name, secretWord })
            onSuccess(updatedGift)
        } catch (requestError) {
            setError(requestError.message || "Не удалось изменить бронь. Попробуйте ещё раз.")
        } finally {
            setIsSubmitting(false)
        }
    }

    return (
        <dialog
            ref={dialogRef}
            className="guest-reservation-modal"
            aria-labelledby="guest-reservation-title"
            onCancel={event => {
                event.preventDefault()
                if (!isSubmitting) onCancel()
            }}
            onClick={event => {
                if (event.target === event.currentTarget && !isSubmitting) onCancel()
            }}
        >
            <form onSubmit={handleSubmit} className="guest-reservation-form">
                <h2 id="guest-reservation-title">
                    {isCancelling ? "Отменить бронь" : "Забронировать подарок"}
                </h2>
                <p>{gift.title}</p>

                {useGuestReservationMocks ? (
                    <>
                        <p className="guest-reservation-demo" role="note">
                            Демо: настоящая бронь не создаётся. Результат сбросится после обновления страницы.
                        </p>
                        {!isCancelling && <label>
                            Ваше имя
                            <input
                                value={name}
                                onChange={event => setName(event.target.value)}
                                autoComplete="name"
                                required
                                disabled={isSubmitting}
                            />
                        </label>}
                        <label>
                            Секретное слово
                            <input
                                type="password"
                                value={secretWord}
                                onChange={event => setSecretWord(event.target.value)}
                                autoComplete="off"
                                aria-describedby="guest-secret-hint"
                                required
                                disabled={isSubmitting}
                            />
                        </label>
                        <p id="guest-secret-hint">
                            {isCancelling
                                ? "Введите то же слово, которое указали при бронировании."
                                : "Запомните слово: оно понадобится, чтобы отменить бронь. Не используйте пароль от аккаунта."}
                        </p>
                    </>
                ) : (
                    <p>Бронь без аккаунта пока недоступна. Для бронирования войдите в аккаунт.</p>
                )}

                {error && <p className="guest-reservation-error" role="alert">{error}</p>}

                <div className="guest-reservation-actions">
                    <button type="button" onClick={onCancel} disabled={isSubmitting}>Закрыть</button>
                    {useGuestReservationMocks
                        ? <button type="submit" disabled={isSubmitting}>
                            {isSubmitting ? "Сохраняем..." : isCancelling ? "Отменить бронь" : "Забронировать"}
                        </button>
                        : <Link to="/auth">Войти</Link>}
                </div>
            </form>
        </dialog>
    )
}

export default GuestReservationModal
