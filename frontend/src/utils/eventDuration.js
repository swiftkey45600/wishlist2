const DAY_MS = 86400000

function calendarDate(value) {
    return value ? new Date(`${value.slice(0, 10)}T00:00:00Z`) : null
}

export function getEventDurationDays(start, end) {
    if (!start || !end) return 1
    const days = Math.floor((calendarDate(end) - calendarDate(start)) / DAY_MS) + 1
    return Number.isFinite(days) && days > 0 ? days : 1
}

export function isValidDuration(days) {
    return Number.isInteger(days) && days >= 1 && days <= 3650
}

export function archiveDay(start, days) {
    if (!start || !isValidDuration(days)) return null
    const date = calendarDate(start)
    date.setUTCDate(date.getUTCDate() + days)
    return Number.isNaN(date.getTime()) ? null : date
}

export function formatArchiveDay(start, days) {
    return archiveDay(start, days)?.toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" }) || ""
}
