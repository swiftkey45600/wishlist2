const giftStatusLabels = {
    available: "Свободен",
    reserved: "Забронирован",
    bought: "Куплен",
}

export function getGiftStatusLabel(status) {
    return giftStatusLabels[status] || "Неизвестен"
}
