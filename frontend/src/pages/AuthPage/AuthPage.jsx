import { useState } from "react"
import { useNavigate } from "react-router-dom"

import "./AuthPage.css"

function AuthPage() {
    const [isLogin, setIsLogin] = useState(true)
    const navigate = useNavigate()

    function handleSubmit() {
        if (isLogin) {
            navigate("/")
        } else {
            navigate("/")
        }
    }

    return (
        <div className="auth-page">
            <div className="auth-card">
                <h1>Wishlist</h1>

                <div className="auth-tabs">
                    <button
                        className={isLogin ? "active-tab" : ""}
                        onClick={() => setIsLogin(true)}
                    >
                        Вход
                    </button>

                    <button
                        className={!isLogin ? "active-tab" : ""}
                        onClick={() => setIsLogin(false)}
                    >
                        Регистрация
                    </button>

                </div>

                <input
                    type="email"
                    placeholder="Email"
                />

                <input
                    type="password"
                    placeholder="Пароль"
                />

                {
                    !isLogin &&
                    <input
                        type="password"
                        placeholder="Повторите пароль"
                    />
                }

                <button 
                    className="submit-button"
                    onClick={handleSubmit}
                >
                    {
                        isLogin
                            ? "Войти"
                            : "Зарегистрироваться"
                    }

                </button>
            </div>
        </div>
    )
}

export default AuthPage
