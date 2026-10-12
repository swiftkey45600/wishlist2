import { useEffect, useState } from "react"
import "./ProfilePage.css"
import "../../styles/common.css"

import Header from "../../components/Header/Header"
import Sidebar from "../../components/Sidebar/Sidebar"
import ProfileCard from "../../components/Profile/ProfileCard/ProfileCard"
import ProfileActions from "../../components/Profile/ProfileActions/ProfileActions"
import { getMe, editMe } from "../../application/userApplication"

const MIN_LOGIN_LENGTH = 3
const MIN_PASSWORD_LENGTH = 8

function isRepeatedCharacter(value) {
    const characters = Array.from(value)
    return characters.length > 0 && characters.every((character) => character === characters[0])
}

function ProfilePage() {
    const [user, setUser] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [name, setName] = useState("")
    const [login, setLogin] = useState("")
    const [password, setPassword] = useState("")
    const [passwordConfirmed, setPasswordConfirmed] = useState("")
    const [editError, setEditError] = useState(null)
    const [isEditOpen, setIsEditOpen] = useState(false)
    const [showSaved, setShowSaved] = useState(false)
    const [isSaving, setIsSaving] = useState(false)

    useEffect(() => {
        async function loadCurrentUser() {
            setLoading(true)
            setError(null)

            const profile = await getMe()
            if (!profile) {
                setError("Не удалось загрузить профиль")
            } else {
                setUser(profile)
                setName(profile.name || "")
                setLogin(profile.login || "")
            }

            setLoading(false)
        }

        loadCurrentUser()
    }, [])

    function openEdit() {
        setName(user?.name || "")
        setLogin(user?.login || "")
        setPassword("")
        setPasswordConfirmed("")
        setEditError(null)
        setIsEditOpen(true)
    }

    async function handleSave() {
        if (!name.trim() || !login.trim()) {
            setEditError("Имя и логин не могут быть пустыми")
            return
        }

        if (Array.from(login.trim()).length < MIN_LOGIN_LENGTH) {
            setEditError(`Логин должен содержать не менее ${MIN_LOGIN_LENGTH} символов`)
            return
        }

        const hasPasswordInput = password.length > 0 || passwordConfirmed.length > 0
        if (hasPasswordInput) {
            if (!password || !passwordConfirmed) {
                setEditError("Введите новый пароль и повторите его")
                return
            }

            if (Array.from(password).length < MIN_PASSWORD_LENGTH) {
                setEditError(`Пароль должен содержать не менее ${MIN_PASSWORD_LENGTH} символов`)
                return
            }

            if (isRepeatedCharacter(password)) {
                setEditError("Пароль не может состоять из одинаковых символов")
                return
            }

            if (password !== passwordConfirmed) {
                setEditError("Пароли не совпадают")
                return
            }
        }

        setEditError(null)
        setShowSaved(false)
        setIsSaving(true)
        const updatedUser = await editMe({
            name: name.trim(),
            login: login.trim(),
            ...(password ? { password } : {})
        })
        setIsSaving(false)

        if (!updatedUser) {
            setEditError("Не удалось обновить профиль")
            return
        }

        setUser(updatedUser)
        setName(updatedUser.name || "")
        setLogin(updatedUser.login || "")
        localStorage.setItem("user", JSON.stringify(updatedUser))
        setPassword("")
        setPasswordConfirmed("")
        setIsEditOpen(false)
        setShowSaved(true)
    }

    return (
        <div className="profile-shell">
            <Header />

            <div className="page-layout">

                <Sidebar />

                <main className="page-content profile-content">
                    <div className="profile-heading">
                        <h1>Профиль</h1>

                        <div className="profile-muted">Информация о вашем аккаунте</div>
                    </div>

                    {loading && <p className="profile-status">Загрузка профиля...</p>}
                    {error && <p className="profile-status error-text">{error}</p>}
                    {!loading && user && (
                        <>
                            <section className="profile-panel">
                                <ProfileCard user={{ ...user, name }} />

                                <div className="profile-section">
                                    <div className="profile-section-head">
                                        <h2>Личные данные</h2>
                                        <button
                                            type="button"
                                            className="profile-button secondary"
                                            onClick={openEdit}
                                        >
                                            Изменить
                                        </button>
                                    </div>

                                    <div className="profile-info-list">
                                        <div><span>Имя</span><strong>{user.name}</strong></div>
                                        <div><span>Логин</span><strong>{user.login}</strong></div>
                                    </div>
                                </div>

                                <div className="profile-section">
                                    <div className="profile-section-head">
                                        <h2>Аккаунт</h2>
                                    </div>
                                    <div className="profile-info-list">
                                        <div><span>Статус</span><strong>Авторизован</strong></div>
                                        <div><span>Авторизация</span><strong>JWT access token</strong></div>
                                        <div><span>Публичный профиль</span><strong>Не используется</strong></div>
                                    </div>
                                </div>

                                <ProfileActions />
                            </section>
                        </>
                    )}
                </main>
            </div>
            {isEditOpen && (
                <div
                    className="profile-edit-overlay"
                    onClick={(event) => {
                        if (event.target === event.currentTarget && !isSaving) setIsEditOpen(false)
                    }}
                >
                    <section
                        className="profile-edit-modal"
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="profile-edit-title"
                    >
                        <div className="profile-edit-head">
                            <h2 id="profile-edit-title">Изменение профиля</h2>
                            <button
                                type="button"
                                className="profile-edit-close"
                                onClick={() => setIsEditOpen(false)}
                                disabled={isSaving}
                            >
                                Закрыть
                            </button>
                        </div>
                        <form className="profile-form" onSubmit={(event) => {
                            event.preventDefault()
                            handleSave()
                        }}>
                            <label className="profile-field">
                                <span>Имя</span>
                                <input
                                    value={name}
                                    onChange={(event) => setName(event.target.value)}
                                    autoComplete="name"
                                />
                            </label>
                            <label className="profile-field">
                                <span>Логин</span>
                                <input
                                    value={login}
                                    onChange={(event) => setLogin(event.target.value)}
                                    autoComplete="username"
                                />
                            </label>
                            <label className="profile-field">
                                <span>Новый пароль</span>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(event) => setPassword(event.target.value)}
                                    autoComplete="new-password"
                                />
                            </label>
                            <label className="profile-field">
                                <span>Повторите новый пароль</span>
                                <input
                                    type="password"
                                    value={passwordConfirmed}
                                    onChange={(event) => setPasswordConfirmed(event.target.value)}
                                    autoComplete="new-password"
                                />
                            </label>
                            <p className="profile-edit-hint">
                                Не менее 8 символов
                            </p>
                            {editError && <p className="profile-edit-error" role="alert">{editError}</p>}
                            <div className="profile-edit-actions">
                                <button
                                    type="button"
                                    className="profile-button secondary"
                                    onClick={() => setIsEditOpen(false)}
                                    disabled={isSaving}
                                >
                                    Отмена
                                </button>
                                <button
                                    type="submit"
                                    className="profile-button primary"
                                    disabled={isSaving}
                                >
                                    {isSaving ? "Сохранение..." : "Сохранить"}
                                </button>
                            </div>
                        </form>
                    </section>
                </div>
            )}
            {showSaved && (
                <div className="profile-toast" onClick={() => setShowSaved(false)}>
                    Изменения профиля сохранены
                </div>
            )}
        </div>
    )
}

export default ProfilePage
