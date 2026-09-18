import { useEffect, useState } from "react"
import "./ProfilePage.css"
import "../../Styles/common.css"

import Header from "../../components/Header/Header"
import Sidebar from "../../components/Sidebar/Sidebar"
import ProfileCard from "../../components/Profile/ProfileCard/ProfileCard"
import ProfileActions from "../../components/Profile/ProfileActions/ProfileActions"
import { getMe, editMe } from "../../application/userApplication"

function ProfilePage() {
    const [user, setUser] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [name, setName] = useState("")
    const [showSaved, setShowSaved] = useState(false)

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
            }

            setLoading(false)
        }

        loadCurrentUser()
    }, [])

    async function handleSave() {
        const updatedUser = await editMe({ name: name.trim() })
        if (!updatedUser) {
            setError("Не удалось обновить профиль")
            return
        }

        setUser(updatedUser)
        setName(updatedUser.name || "")
        localStorage.setItem("user", JSON.stringify(updatedUser))
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
                                        <span className="profile-muted">Профиль</span>
                                    </div>

                                    <div className="profile-form">
                                        <label className="profile-field">
                                            <span>Имя</span>
                                            <input
                                                value={name}
                                                onChange={(event) => setName(event.target.value)}
                                            />
                                        </label>

                                        <label className="profile-field">
                                            <span>Логин</span>
                                            <input value={user.login || ""} readOnly />
                                        </label>

                                        <label className="profile-field profile-field-full">
                                            <span>Пароль</span>
                                            <input value="••••••••••" type="password" readOnly />
                                            <small>Изменение пароля пока недоступно.</small>
                                        </label>
                                    </div>

                                    <div className="profile-actions-row">
                                        <button className="profile-button secondary" disabled>
                                            Изменить пароль
                                        </button>
                                        <button
                                            className="profile-button primary"
                                            onClick={handleSave}
                                        >
                                            Сохранить изменения
                                        </button>
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
            {showSaved && (
                <div className="profile-toast" onClick={() => setShowSaved(false)}>
                    Изменения профиля сохранены
                </div>
            )}
        </div>
    )
}

export default ProfilePage
