import { useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { emailFeaturesEnabled, requestPasswordReset, resetPassword } from "../../repositories/accountEmailRepository"
import "../../pages/AuthPage/AuthPage.css"

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
        } catch {
            setError("Не удалось выполнить запрос. Попробуйте позже.")
        } finally {
            setBusy(false)
        }
    }

    return <div className="auth-page"><div className="auth-card">
        <h1>{reset ? "Новый пароль" : "Восстановление пароля"}</h1>
        {!emailFeaturesEnabled ? <p>Восстановление пароля пока недоступно.</p> : done
            ? <p>{reset ? "Пароль изменён. Войдите с новым паролем." : "Если этот адрес привязан к аккаунту, проверьте почту."}</p>
            : <form className="auth-form" onSubmit={submit}>
                {reset ? <>
                    <input type="password" autoComplete="new-password" placeholder="Новый пароль" value={password} onChange={event => setPassword(event.target.value)} required />
                    <input type="password" autoComplete="new-password" placeholder="Повторите пароль" value={repeat} onChange={event => setRepeat(event.target.value)} required />
                </> : <input type="email" autoComplete="email" placeholder="Электронная почта" value={email} onChange={event => setEmail(event.target.value)} required />}
                {error && <p className="auth-error" role="alert">{error}</p>}
                <button className="submit-button" type="submit" disabled={busy}>{reset ? "Сохранить пароль" : "Запросить письмо"}</button>
            </form>}
        <Link to="/auth">Вернуться ко входу</Link>
    </div></div>
}

export default PasswordRecoveryPage
