import { useState } from "react"
import "./ProfileActions.css"
import LogoutModal from "../LogoutModal/LogoutModal"

function ProfileActions() {
    const [isOpen, setIsOpen] = useState(false)

    return (
        <>
            <div className="profile-actions">
                <h2>Действия</h2>
                <button
                    className="logout-button"
                    onClick={() => setIsOpen(true)}
                >
                    Выйти из аккаунта
                </button>
            </div>

            {isOpen && (
                <LogoutModal onClose={() => setIsOpen(false)} />
            )}
        </>
    )
}

export default ProfileActions
