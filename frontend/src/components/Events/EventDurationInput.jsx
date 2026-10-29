import { useState } from "react"
import { formatArchiveDay } from "../../utils/eventDuration"

const presets = [1, 2, 3, 7, 14, 30]
function dayLabel(days) {
    const last = days % 10, lastTwo = days % 100
    const word = last === 1 && lastTwo !== 11 ? "день" : [2, 3, 4].includes(last) && ![12, 13, 14].includes(lastTwo) ? "дня" : "дней"
    return `${days} ${word}`
}

export default function EventDurationInput({ startDate, value, onChange }) {
    const [custom, setCustom] = useState(() => !presets.includes(value))
    const archive = formatArchiveDay(startDate, value)
    return <div className="event-duration">
        <label className="create-event-field">Длительность события
            <select value={custom ? "custom" : value} disabled={!startDate} onChange={event => {
                setCustom(event.target.value === "custom")
                if (event.target.value !== "custom") onChange(Number(event.target.value))
            }}>
                {presets.map(days => <option key={days} value={days}>{dayLabel(days)}</option>)}
                <option value="custom">Другое количество дней</option>
            </select>
        </label>
        {custom && <label className="create-event-field">Количество дней<input type="number" min="1" max="3650" step="1" value={value || ""} disabled={!startDate} onChange={event => onChange(event.target.value === "" ? 0 : Number(event.target.value))} /></label>}
        <p className="event-duration-hint">{!startDate ? "Выберите дату начала, чтобы настроить автоархивирование." : archive ? `Событие перейдёт в архив ${archive}. Неподаренные желания останутся в «Мои подарки».` : "Укажите длительность от 1 до 3650 дней."}</p>
    </div>
}
