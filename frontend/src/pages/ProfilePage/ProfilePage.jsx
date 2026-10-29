import { useEffect, useState } from "react"
import "./ProfilePage.css"
import "../../styles/common.css"

import { emailFeaturesEnabled, requestEmailVerification, getReminderSettings, setReminderSettings } from "../../repositories/accountEmailRepository"
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
    const [email, setEmail] = useState("")
    const [emailMessage, setEmailMessage] = useState("")
    const [reminders, setReminders] = useState(null)
    const [reminderBusy, setReminderBusy] = useState(false)
    const [reminderError, setReminderError] = useState("")

    useEffect(() => {
        let cancelled = false
        getReminderSettings().then(value => { if (!cancelled) setReminders(value) })
            .catch(() => { if (!cancelled) setReminderError("Не удалось загрузить настройки напоминаний.") })
        return () => { cancelled = true }
    }, [])
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
                setEmail(profile.email || "")
                setName(profile.name || "")
                setLogin(profile.login || "")
            }

            setLoading(false)
        }

        loadCurrentUser()
    }, [])

    function openEdit() {
        setEmail(user?.email || "")
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
            ...(emailFeaturesEnabled ? { email: email.trim() || null } : {}),
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
                                        {emailFeaturesEnabled && <div><span>Почта</span><strong>{user.email || "Не указана"} {user.email && (user.email_verified ? "— подтверждена" : "— не подтверждена")}</strong></div>}
                                    </div>
                                </div>

                                {emailFeaturesEnabled && user.email && !user.email_verified && <button type="button" className="profile-button secondary" onClick={async () => {
                                    setEmailMessage("")
                                    try { await requestEmailVerification(); setEmailMessage("Письмо отправлено. Проверьте почту.") }
                                    catch { setEmailMessage("Не удалось запросить письмо. Попробуйте позже.") }
                                }}>Отправить письмо повторно</button>}
                                {emailMessage && <p role="status">{emailMessage}</p>}
                                <div className="profile-section reminder-settings">
                                    <div className="profile-section-head"><h2>Напоминания о событиях</h2></div>
                                    <p>Одно письмо за день до вашего события или события, на которое вы забронировали подарок.</p>
                                    <label className="reminder-option">
                                        <input type="checkbox" checked={reminders === true}
                                            disabled={reminders === null || reminderBusy || (!user.email_verified && !reminders)}
                                            onChange={async event => {
                                                setReminderBusy(true)
                                                setReminderError("")
                                                try { setReminders(await setReminderSettings(event.target.checked)) }
                                                catch { setReminderError("Не удалось сохранить настройку. Попробуйте ещё раз.") }
                                                finally { setReminderBusy(false) }
                                            }} />
                                        Получать напоминания на почту
                                    </label>
                                    {!user.email_verified && <p>Чтобы включить напоминания, укажите и подтвердите почту.</p>}
                                    {reminderError && <p role="alert">{reminderError}</p>}
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
                            {emailFeaturesEnabled && <label className="profile-field"><span>Электронная почта</span><input type="email" value={email} onChange={event => setEmail(event.target.value)} autoComplete="email" /></label>}
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
