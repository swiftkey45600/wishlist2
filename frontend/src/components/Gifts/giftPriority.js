export const giftPriorityOptions = [
    { value: "high", label: "Очень хочу" },
    { value: "normal", label: "Обычное" },
    { value: "low", label: "На всякий случай" },
]

export function getGiftPriorityLabel(priority) {
    return giftPriorityOptions.find(option => option.value === priority)?.label || "Обычное"
}

export function getGiftPriorityRank(priority) {
    return {
        low: 1,
        normal: 2,
        high: 3,
    }[priority] || 2
}
