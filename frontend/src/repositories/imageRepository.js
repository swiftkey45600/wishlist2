import api from "../services/api"

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
