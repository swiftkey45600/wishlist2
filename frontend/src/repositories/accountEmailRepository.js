import api from "../services/api"

export const emailFeaturesEnabled = true

export async function requestPasswordReset(email) {
    await api.post("/auth/password-reset/request", { email })
}

export async function resetPassword(token, password) {
    await api.post("/auth/password-reset/confirm", { token, new_password: password })
}

export async function requestEmailVerification() {
    await api.post("/auth/email/verification/request")
}
