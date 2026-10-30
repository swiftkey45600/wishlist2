export function todayLocalDate(now = new Date()) {
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, "0")
    const day = String(now.getDate()).padStart(2, "0")
    return `${year}-${month}-${day}`
}

export function currentLocalTime(now = new Date()) {
    return `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`
}

export function isPastEventDate(value, now = new Date()) {
    if (!value) return false
    const [date, time] = value.split("T")
    const today = todayLocalDate(now)
    return date < today || (date === today && Boolean(time) && time.slice(0, 5) < currentLocalTime(now))
}

// Keep the creator's calendar date and UTC offset, so every browser can show the same instant locally.
export function withLocalOffset(value) {
    if (!value) return null
    const local = new Date(value)
    if (Number.isNaN(local.getTime())) return null
    const offset = -local.getTimezoneOffset()
    const sign = offset >= 0 ? "+" : "-"
    const absolute = Math.abs(offset)
    return `${value}${sign}${String(Math.floor(absolute / 60)).padStart(2, "0")}:${String(absolute % 60).padStart(2, "0")}`
}
