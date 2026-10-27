import api from "../services/api"

// Proposed API; enable only after the backend implements this contract.
export const emailFeaturesEnabled = import.meta.env.VITE_ACCOUNT_EMAIL_ENABLED === "true"

export async function requestPasswordReset(email) {
    await api.post("/auth/password-reset/request", { email })
}

export async function resetPassword(token, password) {
    await api.post("/auth/password-reset/confirm", { token, password })
}

export async function requestEmailVerification() {
    await api.post("/auth/email/verification")
}
