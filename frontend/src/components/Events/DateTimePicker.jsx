import { useState } from "react"
import "./DateTimePicker.css"
import { currentLocalTime, todayLocalDate } from "../../utils/eventDate"

const hours = Array.from({ length: 24 }, (_, index) => String(index).padStart(2, "0"))
const minutes = Array.from({ length: 60 }, (_, index) => String(index).padStart(2, "0"))

function DateTimePicker({ value = "", onChange, min, onBlur }) {
    const [draftTime, setDraftTime] = useState("12:00")
    const date = value.split("T")[0]
    const time = value.includes("T") ? value.split("T")[1].slice(0, 5) : draftTime
    const [hour, minute] = time.split(":")
    const now = new Date()
    const minimumTime = date === todayLocalDate(now) ? currentLocalTime(now) : null
    const [minimumHour, minimumMinute] = (minimumTime || "00:00").split(":")

    function changeDate(nextDate) {
        const currentTime = currentLocalTime()
        const selectedTime = nextDate === todayLocalDate() && time < currentTime ? currentTime : time
        setDraftTime(selectedTime)
        onChange({ target: { value: nextDate ? `${nextDate}T${selectedTime}` : "" } })
    }

    function changeTime(nextTime) {
        const currentTime = currentLocalTime()
        const selectedTime = date === todayLocalDate() && nextTime < currentTime ? currentTime : nextTime
        setDraftTime(selectedTime)
        if (date) onChange({ target: { value: `${date}T${selectedTime}` } })
    }

    return <div className="event-datetime" onBlur={event => {
        if (!event.currentTarget.contains(event.relatedTarget)) onBlur?.(event)
    }}>
        <input type="date" aria-label="Дата события" value={date} min={min?.split("T")[0]}
            onChange={event => changeDate(event.target.value)} />
        <div className="event-time" role="group" aria-label="Время события">
            <select aria-label="Часы" value={hour} onChange={event => changeTime(`${event.target.value}:${minute}`)}>
                {hours.map(item => <option key={item} value={item} disabled={Boolean(minimumTime) && item < minimumHour}>{item}</option>)}
            </select>
            <span aria-hidden="true">:</span>
            <select aria-label="Минуты" value={minute} onChange={event => changeTime(`${hour}:${event.target.value}`)}>
                {minutes.map(item => <option key={item} value={item} disabled={Boolean(minimumTime) && hour === minimumHour && item < minimumMinute}>{item}</option>)}
            </select>
        </div>
    </div>
}
export default DateTimePicker
