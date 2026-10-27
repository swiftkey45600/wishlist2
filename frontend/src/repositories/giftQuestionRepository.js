import api from "../services/api"

function questionsPath(token, giftId) {
    return `/events/public/${encodeURIComponent(token)}/gifts/${giftId}/questions`
}

export async function fetchQuestions(token, giftId) {
    const response = await api.get(questionsPath(token, giftId))
    return response.data
}

export async function createQuestion(token, giftId, guestName, text) {
    const response = await api.post(questionsPath(token, giftId), { guest_name: guestName, text })
    return response.data
}

export async function answerQuestion(giftId, questionId, answer) {
    const response = await api.patch(`/gifts/${giftId}/questions/${questionId}/answer`, { answer })
    return response.data
}
