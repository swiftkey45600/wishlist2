import { useState } from "react"
import { useNavigate } from "react-router-dom"

import {
    login,
    register
} from "../../application/authApplication"

import "./AuthPage.css"

function AuthPage() {
    const [isLogin, setIsLogin] = useState(true)
    const [name, setName] = useState("")
    const [loginValue, setLoginValue] = useState("")
    const [password, setPassword] = useState("")
    const [passwordConfirmed, setPasswordConfirmed] = useState("")
    const [error, setError] = useState(null)
    const [isSubmitting, setIsSubmitting] = useState(false)

    const navigate = useNavigate()

    async function handleSubmit(event) {
        event.preventDefault()
        setError(null)

        if (!loginValue.trim() || !password) {
            setError("Заполните логин и пароль")
            return
        }

        if (!isLogin) {
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
                ? await login({ login: loginValue, password })
                : await register({ name, login: loginValue, password })

            if (response?.access_token) {
                localStorage.setItem("accessToken", response.access_token)
                localStorage.setItem("user", JSON.stringify(response.user))
            }

            navigate("/")
        } catch (submitError) {
            const message = submitError?.response?.data?.detail || submitError?.message || "Ошибка авторизации"
            setError(message)
        } finally {
            setIsSubmitting(false)
        }
    }

    return (
        <div className="auth-page">
            <div className="auth-card">
                <h1>Wishlist</h1>

                <div className="auth-tabs">
                    <button
                        className={isLogin ? "active-tab" : ""}
                        onClick={() => {
                            setIsLogin(true)
                            setError(null)
                        }}
                    >
                        Вход
                    </button>

                    <button
                        className={!isLogin ? "active-tab" : ""}
                        onClick={() => {
                            setIsLogin(false)
                            setError(null)
                        }}
                    >
                        Регистрация
                    </button>
                </div>

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

                    {error && <p className="auth-error">{error}</p>}

                    <button
                        type="submit"
                        className="submit-button"
                        disabled={isSubmitting}
                    >
                        {isLogin ? "Войти" : "Зарегистрироваться"}
                    </button>
                </form>
            </div>
        </div>
    )
}

export default AuthPage
