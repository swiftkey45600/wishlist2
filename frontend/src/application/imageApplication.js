import {
    createImage as createImageRepository,
    getImage as getImageRepository,
    deleteImage as deleteImageRepository,
    resolveImageUrl as resolveImageUrlRepository
} from "../repositories/imageRepository"

export function resolveImageUrl(imageId, imageUrl) {
    return resolveImageUrlRepository(imageId, imageUrl)
}

export async function createImage(imageData) {
    try {
        return await createImageRepository(imageData)
    } catch (error) {
        console.error(error)
        return null
    }
}

export async function uploadImageFile(file) {
    const imageData = new FormData()
    imageData.append("file", file)
    return await createImage(imageData)
}

export async function getImage(imageId) {
    try {
        return await getImageRepository(imageId)
    } catch (error) {
        console.error(error)
        return null
    }
}

export async function deleteImage(imageId) {
    try {
        return await deleteImageRepository(imageId)
    } catch (error) {
        console.error(error)
        return null
    }
}
