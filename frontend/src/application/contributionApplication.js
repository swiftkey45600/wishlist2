import {
    fetchContributions,
    createContribution,
    deleteContribution
} from "../repositories/contributionRepository"

function contributionError(error) {
    const status = error.response?.status
    const detail = error.response?.data?.detail
    if (status === 429) {
        const seconds = Number(error.response.headers?.["retry-after"])
        return new Error(Number.isFinite(seconds) && seconds > 0
            ? `Слишком много попыток. Повторите через ${seconds} сек.`
            : "Слишком много попыток. Повторите через минуту.")
    }
    const messages = {
        "Invalid secret word": "Неверное секретное слово.",
        "You can only cancel your own contribution": "Можно отменить только свой взнос.",
        "Contribution exceeds the remaining fundraising goal": "Сумма превышает остаток до цели. Обновите сбор и проверьте сумму.",
        "Gift is not available for contributions": "Сбор уже завершён или подарок недоступен для взносов.",
        "Contributions to a bought gift cannot be cancelled": "Подарок уже куплен, отменить взнос нельзя.",
        "Fundraising is not enabled for this gift": "Сбор на этот подарок отключён.",
        "Name and secret word are required for guest contributions": "Введите имя и секретное слово. Если сессия закончилась, войдите снова."
    }
    if (messages[detail]) return new Error(messages[detail], { cause: error })
    if (status === 409) return new Error("Не удалось добавить взнос. Событие могло завершиться или сбор изменился.", { cause: error })
    if (status === 404) return new Error("Подарок или взнос не найден. Обновите страницу.")
    if (status === 403) return new Error("Нет доступа к этому сбору.")
    if (status === 422) return new Error("Проверьте сумму, имя и секретное слово.")
    return new Error("Не удалось обновить сбор. Попробуйте ещё раз.")
}

export function parseContributionGoal(value, collected = 0) {
    if (value === null || value === undefined) {
        if (collected > 0) throw new Error("Сбор со взносами нельзя отключить.")
        return null
    }
    const amount = Number(value)
    if (!Number.isSafeInteger(amount) || amount <= 0) {
        throw new Error("Введите положительную цель в целых рублях.")
    }
    if (amount < collected) throw new Error("Цель не может быть меньше собранной суммы.")
    return amount
}

export async function getContributions(giftId, publicToken) {
    try {
        return await fetchContributions(giftId, publicToken)
    } catch (error) {
        throw contributionError(error)
    }
}

export async function addContribution(publicToken, giftId, data) {
    try {
        return await createContribution(publicToken, giftId, data)
    } catch (error) {
        throw contributionError(error)
    }
}

export async function cancelContribution(publicToken, giftId, contributionId, secretWord) {
    try {
        return await deleteContribution(publicToken, giftId, contributionId, secretWord)
    } catch (error) {
        throw contributionError(error)
    }
}
