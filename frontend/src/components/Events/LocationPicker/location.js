const coordinatesPattern = /\s*\(координаты: (-?\d+\.\d+), (-?\d+\.\d+)\)$/
export function getLocationCoordinates(value) {
    const match = (value || "").match(coordinatesPattern)
    return match ? [Number(match[1]), Number(match[2])] : null
}
export function withoutLocationCoordinates(value) {
    return (value || "").replace(coordinatesPattern, "").trim()
}
