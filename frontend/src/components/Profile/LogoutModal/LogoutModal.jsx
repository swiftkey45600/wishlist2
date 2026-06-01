import "./LogoutModal.css"

import { useNavigate } from "react-router-dom"

function LogoutModal({
    onClose
}) {
    const navigate = useNavigate()

    function handleLogout() {
       navigate("/auth")
    }

    return (
        <div className="modal-overlay">
            <div className="logout-modal">
                <h2> Выход из аккаунта </h2>

                <p> Вы уверены, что хотите выйти? </p>

                <div className="logout-actions">
                    <button
                        className="cancel-button"
                        onClick={onClose}
                    >
                        Отмена
                    </button>

                    <button 
                        className="confirm-logout-button"
                        onClick={handleLogout}    
                    >
                        Выйти
                    </button>

                </div>
            </div>
        </div>
    )
}

export default LogoutModal
