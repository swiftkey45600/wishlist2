import * as authRepository from "../repositories/authRepository"

export async function login(userData) {
    return await authRepository.loginUser(userData)
}

export async function register(userData) {
    return await authRepository.registerUser(userData)
}
