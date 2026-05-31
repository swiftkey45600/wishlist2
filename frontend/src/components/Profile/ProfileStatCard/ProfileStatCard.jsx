import "./ProfileStatCard.css"

function ProfileStatCard({
    value,
    title,
    description
}) {
    return (
        <div className="profile-stat-card">
            <h2>{value}</h2>
            <h3>{title}</h3>
            <p>{description}</p>
        </div>
    )
}

export default ProfileStatCard
