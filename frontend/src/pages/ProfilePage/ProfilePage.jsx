import { useEffect, useState } from "react"
import "./ProfilePage.css"
import "../../Styles/common.css"

import Sidebar from "../../components/Sidebar/Sidebar"
import ProfileCard from "../../components/Profile/ProfileCard/ProfileCard"
import ProfileActions from "../../components/Profile/ProfileActions/ProfileActions"
import { getMe } from "../../application/userApplication"

function ProfilePage() {
    const [user, setUser] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        async function loadCurrentUser() {
            setLoading(true)
            setError(null)

            const profile = await getMe()
            if (!profile) {
                setError("Не удалось загрузить профиль")
            } else {
                setUser(profile)
            }

            setLoading(false)
        }

        loadCurrentUser()
    }, [])

    return (
        <div className="page-layout">
            <Sidebar />
            <div className="page-content">
                <div className="page-header">
                    <h1>Мой профиль</h1>
                    <p>Управляйте аккаунтом и просматривайте активность</p>
                </div>

                {loading && <p>Загрузка профиля...</p>}
                {error && <p className="error-text">{error}</p>}
                {!loading && user && (
                    <>
                        <ProfileCard user={user} />
                        <ProfileActions user={user} />
                    </>
                )}
            </div>
        </div>
    )
}

export default ProfilePage
