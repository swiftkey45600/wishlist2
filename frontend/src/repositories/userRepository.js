import api from "../services/api"

const getAuthHeaders = () => {
    const token = localStorage.getItem("accessToken")
    return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function getUsers() {
    const response = await api.get("/users/", { headers: getAuthHeaders() })
    return response.data.users
}

export async function getMe() {
    const response = await api.get("/users/me", { headers: getAuthHeaders() })
    return response.data.user
}

export async function getUser(userId) {
    const response = await api.get(`/users/${userId}`, { headers: getAuthHeaders() })
    return response.data.user
}

export async function deleteUser(userId) {
    const response = await api.delete(`/users/${userId}`, { headers: getAuthHeaders() })
    return response.data
}
