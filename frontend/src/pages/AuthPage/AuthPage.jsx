import { YandexButton } from "../../components/YandexAuth/YandexAuth"
import SegmentedControl from "../../components/SegmentedControl/SegmentedControl"
import { useState } from "react"
import { Link, useNavigate, useSearchParams } from "react-router-dom"
import { Gift, Heart, Sparkles } from "lucide-react"
import { emailFeaturesEnabled } from "../../repositories/accountEmailRepository"

import {
    login,
    register
} from "../../application/authApplication"

import "./AuthPage.css"

const MIN_LOGIN_LENGTH = 3
const MIN_PASSWORD_LENGTH = 8

function isRepeatedCharacter(value) {
    const characters = Array.from(value)
    return characters.length > 0 && characters.every((character) => character === characters[0])
}

function AuthPage() {
    const [isLogin, setIsLogin] = useState(true)
    const [email, setEmail] = useState("")
    const [name, setName] = useState("")
    const [loginValue, setLoginValue] = useState("")
    const [password, setPassword] = useState("")
    const [passwordConfirmed, setPasswordConfirmed] = useState("")
    const [error, setError] = useState(null)
    const [isSubmitting, setIsSubmitting] = useState(false)

    const navigate = useNavigate()
    const [params] = useSearchParams()

    async function handleSubmit(event) {
        event.preventDefault()
        setError(null)

        if (!loginValue.trim() || !password) {
            setError("Заполните логин и пароль")
            return
        }

        if (!isLogin) {
            if (Array.from(loginValue.trim()).length < MIN_LOGIN_LENGTH) {
                setError(`Логин должен содержать не менее ${MIN_LOGIN_LENGTH} символов`)
                return
            }

            if (Array.from(password).length < MIN_PASSWORD_LENGTH) {
                setError(`Пароль должен содержать не менее ${MIN_PASSWORD_LENGTH} символов`)
                return
            }

            if (isRepeatedCharacter(password)) {
                setError("Пароль не может состоять из одинаковых символов")
                return
            }

            if (!name.trim()) {
                setError("Введите имя")
                return
            }

            if (password !== passwordConfirmed) {
                setError("Пароли не совпадают")
                return
            }
        }

        setIsSubmitting(true)

        try {
            const response = isLogin
                ? await login({ login: loginValue.trim(), password })
                : await register({ name, login: loginValue.trim(), password, ...(emailFeaturesEnabled ? { email: email.trim() } : {}) })

            if (!response?.access_token) {
                setError("Не удалось подтвердить авторизацию")
                return
            }

            localStorage.setItem("accessToken", response.access_token)
            localStorage.setItem("user", JSON.stringify(response.user))
            const next = params.get("next") || ""
            navigate(next.startsWith("/wishes/shared/") && !next.startsWith("//") ? next : "/", { replace: true })
        } catch (submitError) {
            const detail = submitError?.response?.data?.detail
            const messages = {
                "Login already exists": "Этот логин уже занят. Попробуйте другой.",
                "No user with this login": "Пользователь с таким логином не найден.",
                "Invalid password": "Неверный пароль. Проверьте введенные данные.",
                "Invalid login or password": "Неверный логин или пароль."
            }
            const message = typeof detail === "string"
                ? messages[detail] || detail
                : "Не удалось выполнить авторизацию. Проверьте подключение и попробуйте снова."
            setError(message)
        } finally {
            setIsSubmitting(false)
        }
    }

    return (
        <div className="auth-page">
            <div className="auth-layout">
                <section className="auth-welcome" aria-label="О Wishlist">
                    <div className="auth-brand"><span><Heart size={22} fill="currentColor" /></span> Wishlist</div>
                    <div className="auth-welcome-content">
                        <span className="auth-eyebrow"><Sparkles size={15} /> ПОВОДЫ ДЛЯ РАДОСТИ</span>
                        <h1>Желания, которые<br />сближают</h1>
                        <p>Собирайте идеи подарков и делитесь ими с теми, кто вам дорог.</p>
                        <div className="auth-wish-card"><span className="auth-gift-icon"><Gift size={23} /></span><div><strong>Всё, о чём мечтается</strong><small>В одном красивом месте</small></div><Heart size={18} /></div>
                    </div>
                    <span className="auth-welcome-footer">Ваше пространство для особенных моментов ✨</span>
                </section>
            <div className="auth-card">
                <div className="auth-card-heading"><span>ВАШЕ ПРОСТРАНСТВО</span><h2>{isLogin ? "С возвращением" : "Присоединяйтесь"}</h2><p>{isLogin ? "Войдите, чтобы открыть свои желания" : "Создайте свой первый список желаний"}</p></div>

                <SegmentedControl label="Вход или регистрация" value={isLogin}
                    onChange={value => { setIsLogin(value); setError(null) }}
                    options={[{ value: true, label: "Вход" }, { value: false, label: "Регистрация" }]} />

                <form className="auth-form" onSubmit={handleSubmit}>
                    {
                        !isLogin &&
                        <input
                            type="text"
                            placeholder="Имя"
                            value={name}
                            onChange={(event) => setName(event.target.value)}
                        />
                    }

                    {!isLogin && emailFeaturesEnabled && <input type="email" placeholder="Электронная почта" autoComplete="email" value={email} onChange={event => setEmail(event.target.value)} required />}

                    <input
                        type="text"
                        placeholder="Логин"
                        value={loginValue}
                        onChange={(event) => setLoginValue(event.target.value)}
                    />

                    <input
                        type="password"
                        placeholder="Пароль"
                        value={password}
                        onChange={(event) => setPassword(event.target.value)}
                    />

                    {
                        !isLogin &&
                        <input
                            type="password"
                            placeholder="Повторите пароль"
                            value={passwordConfirmed}
                            onChange={(event) => setPasswordConfirmed(event.target.value)}
                        />
                    }

                    {isLogin && emailFeaturesEnabled && <Link to="/forgot-password">Забыли пароль?</Link>}
                    {error && <p className="auth-error">{error}</p>}

                    <button
                        type="submit"
                        className="submit-button"
                        disabled={isSubmitting}
                    >
                        {isLogin ? "Войти" : "Зарегистрироваться"}
                    </button>
                </form>
                <YandexButton next={params.get("next") || ""} />
            </div>
            </div>
        </div>
    )
}

export default AuthPage
