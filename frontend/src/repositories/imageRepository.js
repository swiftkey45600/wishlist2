import api from "../services/api"

function getApiBaseUrl() {
    const baseUrl = new URL(api.defaults.baseURL || "/", window.location.origin)
    baseUrl.pathname = `${baseUrl.pathname.replace(/\/+$/, "")}/`
    return baseUrl
}

export function resolveImageUrl(imageId, imageUrl) {
    if (imageId) {
        return new URL(`images/${encodeURIComponent(imageId)}`, getApiBaseUrl()).toString()
    }
    if (!imageUrl) return ""

    const apiBaseUrl = getApiBaseUrl()
    try {
        return new URL(imageUrl).toString()
    } catch {
        return new URL(imageUrl.replace(/^\/+/, ""), apiBaseUrl).toString()
    }
}

export async function createImage(imageData) {
    const response = await api.post("/images", imageData)
    return response.data
}

export async function getImage(imageId) {
    const response = await api.get(`/images/${imageId}`, {
        responseType: "blob"
    })

    return response.data
}

export async function deleteImage(imageId) {
    const response = await api.delete(`/images/${imageId}`)
    return response.data
}
