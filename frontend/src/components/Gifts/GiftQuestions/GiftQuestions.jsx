import { useEffect, useState } from "react"
import { answerQuestion, createQuestion, fetchQuestions } from "../../../repositories/giftQuestionRepository"
import "./GiftQuestions.css"

function GiftQuestions({ token, giftId, isOwner }) {
    const [questions, setQuestions] = useState(null)
    const [open, setOpen] = useState(false)
    const [name, setName] = useState("")
    const [text, setText] = useState("")
    const [answers, setAnswers] = useState({})
    const [error, setError] = useState("")
    const [busy, setBusy] = useState(false)
    const [attempt, setAttempt] = useState(0)

    useEffect(() => {
        let cancelled = false
        fetchQuestions(token, giftId).then(data => {
            if (!cancelled) {
                setQuestions(data)
                setError("")
            }
        }).catch(() => {
            if (!cancelled) setError("Не удалось загрузить вопросы.")
        })
        return () => { cancelled = true }
    }, [token, giftId, attempt])

    async function submitQuestion(event) {
        event.preventDefault()
        if (!name.trim() || !text.trim() || busy) return
        setBusy(true)
        setError("")
        try {
            const question = await createQuestion(token, giftId, name.trim(), text.trim())
            setQuestions(current => [...current, question])
            setText("")
        } catch (err) {
            setError(err.response?.status === 429 ? "Слишком много вопросов. Попробуйте позже." : "Не удалось отправить вопрос.")
        } finally {
            setBusy(false)
        }
    }

    async function submitAnswer(event, question) {
        event.preventDefault()
        const answer = (answers[question.id] ?? question.answer ?? "").trim()
        if (!answer || busy) return
        setBusy(true)
        setError("")
        try {
            const updated = await answerQuestion(giftId, question.id, answer)
            setQuestions(current => current.map(item => item.id === updated.id ? updated : item))
            setAnswers(current => ({ ...current, [question.id]: updated.answer }))
        } catch {
            setError("Не удалось сохранить ответ.")
        } finally {
            setBusy(false)
        }
    }

    return <section className="gift-questions">
        <button type="button" className="gift-secondary-button" aria-expanded={open} onClick={() => setOpen(value => !value)}>
            Вопросы о подарке{questions && ` (${questions.length})`}
        </button>
        {open && <div className="gift-questions-content">
            {error && <p className="gift-questions-error" role="alert">{error} {!questions && <button type="button" onClick={() => setAttempt(value => value + 1)}>Повторить</button>}</p>}
            {!questions && !error && <p>Загружаем вопросы...</p>}
            {questions && <>
                {questions.length === 0 && <p>Пока нет вопросов.</p>}
                {isOwner && questions.length > 0 && <p>Без ответа: {questions.filter(question => !question.answer).length}</p>}
                {questions.map(question => <div className="gift-question" key={question.id}>
                    <strong>{question.guest_name}</strong>
                    <p>{question.text}</p>
                    {question.answer && <p><strong>Ответ владельца:</strong> {question.answer}</p>}
                    {isOwner && <form onSubmit={event => submitAnswer(event, question)}>
                        <label>Ваш ответ
                            <textarea value={answers[question.id] ?? question.answer ?? ""} onChange={event => setAnswers(current => ({ ...current, [question.id]: event.target.value }))} maxLength={2000} required />
                        </label>
                        <button className="gift-secondary-button" type="submit" disabled={busy}>Сохранить ответ</button>
                    </form>}
                </div>)}
                {!isOwner && <form onSubmit={submitQuestion}>
                    <label>Ваше имя<input value={name} onChange={event => setName(event.target.value)} maxLength={100} required /></label>
                    <label>Вопрос<textarea value={text} onChange={event => setText(event.target.value)} maxLength={2000} placeholder="Какой размер, цвет или модель?" required /></label>
                    <button className="gift-secondary-button" type="submit" disabled={busy}>Задать вопрос</button>
                </form>}
            </>}
        </div>}
    </section>
}

export default GiftQuestions
