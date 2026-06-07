import {
    getUsers as getUsersRepository,
    getMe as getMeRepository,
    getUser as getUserRepository,
    deleteUser as deleteUserRepository
} from "../repositories/userRepository"

export async function getUsers() {
    try {
        return await getUsersRepository()
    } catch (error) {
        console.error(error)
        return []
    }
}

export async function getMe() {
    try {
        return await getMeRepository()
    } catch (error) {
        console.error(error)
        return null
    }
}

export async function getUser(userId) {
    try {
        return await getUserRepository(userId)
    } catch (error) {
        console.error(error)
        return null
    }
}

export async function deleteUser(userId) {
    try {
        return await deleteUserRepository(userId)
    } catch (error) {
        console.error(error)
        return null
    }
}
