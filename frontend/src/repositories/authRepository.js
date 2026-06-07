import api from "../services/api"

export async function loginUser(userData) {
    const response = await api.post("/auth/login", {
        login: userData.login,
        password: userData.password
    })

    return response.data
}

export async function registerUser(userData) {
    const response = await api.post("/auth/register", {
        name: userData.name,
        login: userData.login,
        password: userData.password
    })

    return response.data
}
