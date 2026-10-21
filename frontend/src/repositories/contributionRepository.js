import api from "../services/api"

export async function fetchContributions(giftId, publicToken) {
    const path = publicToken
        ? `/events/public/${publicToken}/gifts/${giftId}/contributions`
        : `/gifts/${giftId}/contributions`
    const response = await api.get(path)
    return response.data
}

export async function createContribution(publicToken, giftId, data) {
    const response = await api.post(`/events/public/${publicToken}/gifts/${giftId}/contributions`, data)
    return response.data
}

export async function deleteContribution(publicToken, giftId, contributionId, secretWord) {
    const response = await api.delete(
        `/events/public/${publicToken}/gifts/${giftId}/contributions/${contributionId}`,
        secretWord === undefined ? {} : { data: { secret_word: secretWord } }
    )
    return response.data
}
