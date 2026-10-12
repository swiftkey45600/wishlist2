import api from "../services/api"

export function resolveImageUrl(imageId, imageUrl) {
    const imagePath = imageId ? `/images/${imageId}` : imageUrl
    if (!imagePath) return ""

    return new URL(imagePath, api.defaults.baseURL).toString()
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
