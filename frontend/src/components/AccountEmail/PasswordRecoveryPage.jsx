import { useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { ArrowLeft, CircleCheck, Heart, LockKeyhole, Mail } from "lucide-react"
import { emailFeaturesEnabled, requestPasswordReset, resetPassword } from "../../repositories/accountEmailRepository"
import "../../pages/AuthPage/AuthPage.css"
import "./AccountEmail.css"

function PasswordRecoveryPage({ reset = false }) {
    const [params] = useSearchParams()
    const token = params.get("token") || ""
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [repeat, setRepeat] = useState("")
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState("")
    const [done, setDone] = useState(false)

    async function submit(event) {
        event.preventDefault()
        setError("")
        if (reset && (!token || password.length < 8 || password !== repeat)) {
            setError(!token ? "Ссылка недействительна." : "Пароли должны совпадать и содержать не менее 8 символов.")
            return
        }
        setBusy(true)
        try {
            if (reset) await resetPassword(token, password)
            else await requestPasswordReset(email.trim())
            setDone(true)
        } catch (requestError) {
            const status = requestError.response?.status
            setError(status === 429 ? "Слишком много запросов. Подождите и попробуйте позже."
                : reset && status === 400 ? "Ссылка недействительна, просрочена или уже использована. Запросите новую."
                    : "Не удалось выполнить запрос. Попробуйте позже.")
        } finally {
            setBusy(false)
        }
    }

    return <div className="auth-page account-email-page"><main className="auth-card account-email-card">
        <div className="auth-brand"><span><Heart size={22} fill="currentColor" /></span> Wishlist</div>
        <div className={`account-email-icon${done ? " success" : ""}`} aria-hidden="true">
            {done ? <CircleCheck size={27} /> : reset ? <LockKeyhole size={26} /> : <Mail size={26} />}
        </div>
        <div className="account-email-heading">
            <h1>{done ? (reset ? "Пароль изменён" : "Проверьте почту") : reset ? "Новый пароль" : "Забыли пароль?"}</h1>
            <p>{done ? (reset ? "Всё готово! Войдите в Wishlist с новым паролем."
                : "Если этот адрес привязан к аккаунту и подтверждён, на него придёт письмо со ссылкой для сброса пароля.")
                : reset ? "Задайте новый пароль для вашего аккаунта Wishlist."
                    : "Введите подтверждённый email вашего аккаунта. Мы отправим ссылку для смены пароля."}</p>
        </div>
        {!emailFeaturesEnabled ? <p role="status">Восстановление пароля пока недоступно.</p> : done
            ? <p className="account-email-hint" role="status">{reset ? "После смены пароля нужно войти заново на всех устройствах." : "Если письма нет, проверьте папку «Спам». Ссылка действует 30 минут."}</p>
            : <form className="auth-form" onSubmit={submit}>
                {reset ? <>
                    <label>Новый пароль<input type="password" autoComplete="new-password" placeholder="Не менее 8 символов" minLength={8} value={password} onChange={event => setPassword(event.target.value)} disabled={busy} required /></label>
                    <label>Повторите пароль<input type="password" autoComplete="new-password" placeholder="Введите пароль ещё раз" minLength={8} value={repeat} onChange={event => setRepeat(event.target.value)} disabled={busy} required /></label>
                </> : <label>Электронная почта<input type="email" autoComplete="email" placeholder="name@example.com" maxLength={254} value={email} onChange={event => setEmail(event.target.value)} disabled={busy} required /></label>}
                {error && <p className="auth-error" role="alert">{error}</p>}
                <button className="submit-button" type="submit" disabled={busy}>{busy ? "Подождите…" : reset ? "Сохранить пароль" : "Отправить ссылку"}</button>
            </form>}
        <Link className="account-email-back" to="/auth"><ArrowLeft size={16} aria-hidden="true" /> Вернуться ко входу</Link>
    </main></div>
}

export default PasswordRecoveryPage
