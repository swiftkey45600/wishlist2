import "./ProfilePage.css"
import "../../Styles/common.css"

import Sidebar from "../../components/Sidebar/Sidebar";
import ProfileCard from "../../components/Profile/ProfileCard/ProfileCard"
import ProfileActions from "../../components/Profile/ProfileActions/ProfileActions"

function ProfilePage() {
    return (
        <div className="page-layout">
            <Sidebar />
            <div className="page-content">
                <div className="page-header">
                    <h1>Мой профиль</h1>
                    <p>Управляйте аккаунтом и просматривайте активность</p>
                </div>

                <ProfileCard />
                <ProfileActions />
            </div>
        </div>
    )
}

export default ProfilePage
