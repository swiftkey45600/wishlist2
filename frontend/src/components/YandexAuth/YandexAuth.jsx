import { useEffect, useRef, useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import api from "../../services/api"
import "./YandexAuth.css"

const stateKey = "wishlist.yandex.state"
const nextKey = "wishlist.yandex.next"
const proofKey = "wishlist.yandex.proof"

export function YandexButton({ link = false, next = "" }) {
    const [enabled, setEnabled] = useState(false)
    const [error, setError] = useState("")
    const [busy, setBusy] = useState(false)
    useEffect(() => {
        let active = true
        api.get("/auth/yandex/availability").then(response => { if (active) setEnabled(response.data.enabled) }).catch(() => {})
        return () => { active = false }
    }, [])
    if (!enabled) return null
    async function start() {
        setBusy(true)
        setError("")
        try {
            const response = await api.post("/auth/yandex/start", { link })
            sessionStorage.setItem(stateKey, response.data.state)
            sessionStorage.setItem(proofKey, response.data.proof)
            sessionStorage.setItem(nextKey, link ? "/profile" : (next.startsWith("/wishes/shared/") && !next.startsWith("//") ? next : "/"))
            window.location.assign(response.data.url)
        } catch {
            setError("Не удалось открыть Яндекс ID. Попробуйте ещё раз.")
            setBusy(false)
        }
    }
    return <div className="yandex-auth"><button type="button" className="yandex-auth-button" onClick={start} disabled={busy}>
        <span className="yandex-auth-mark" aria-hidden="true">Я</span>{link ? "Привязать Яндекс ID" : "Войти с Яндекс ID"}
    </button>{error && <p role="alert">{error}</p>}</div>
}

export function YandexCallback() {
    const navigate = useNavigate()
    const handled = useRef(false)
    const [error, setError] = useState(() => {
        const params = new URLSearchParams(window.location.search)
        const expected = sessionStorage.getItem(stateKey)
        return expected && sessionStorage.getItem(proofKey) && params.get("state") === expected && params.get("code")
            ? "" : "Вход отменён или время ожидания истекло. Попробуйте ещё раз."
    })
    useEffect(() => {
        if (handled.current) return
        handled.current = true
        const params = new URLSearchParams(window.location.search)
        const state = params.get("state")
        const code = params.get("code")
        const expected = sessionStorage.getItem(stateKey)
        const proof = sessionStorage.getItem(proofKey)
        const next = sessionStorage.getItem(nextKey) || "/"
        sessionStorage.removeItem(stateKey)
        sessionStorage.removeItem(proofKey)
        sessionStorage.removeItem(nextKey)
        window.history.replaceState(null, "", "/auth/yandex")
        if (!expected || !proof || !state || state !== expected || !code) {
            return
        }
        api.post("/auth/yandex/exchange", { state, code, proof }).then(response => {
            localStorage.setItem("accessToken", response.data.access_token)
            localStorage.setItem("user", JSON.stringify(response.data.user))
            navigate(next === "/profile" || (next.startsWith("/wishes/shared/") && !next.startsWith("//")) ? next : "/", { replace: true })
        }).catch(requestError => {
            setError(requestError.response?.status === 409
                ? "Этот Яндекс ID уже привязан к другому аккаунту."
                : "Не удалось завершить вход. Попробуйте ещё раз.")
        })
    }, [navigate])
    return <main className="yandex-callback"><h1>Яндекс ID</h1>{error ? <><p role="alert">{error}</p><Link to="/auth">Вернуться ко входу</Link></> : <p role="status">Завершаем вход…</p>}</main>
}
