import {
    createImage as createImageRepository,
    getImage as getImageRepository,
    deleteImage as deleteImageRepository
} from "../repositories/imageRepository"

export async function createImage(imageData) {
    try {
        return await createImageRepository(imageData)
    } catch (error) {
        console.error(error)
        return null
    }
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
