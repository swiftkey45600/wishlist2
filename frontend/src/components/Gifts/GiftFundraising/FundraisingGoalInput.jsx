import { useId } from "react"
import "./GiftFundraising.css"

function FundraisingGoalInput({ value, onChange, defaultGoal, collected = 0, error, disabled = false }) {
    const id = useId()
    const enabled = value !== null && value !== undefined

    return (
        <div className="fundraising-goal">
            <label className="fundraising-toggle">
                <input
                    type="checkbox"
                    checked={enabled}
                    disabled={disabled || collected > 0}
                    onChange={event => onChange(event.target.checked ? String(defaultGoal || "") : null)}
                />
                Совместный сбор на подарок
            </label>
            {enabled && <>
                <label htmlFor={id}>Цель сбора, ₽</label>
                <input
                    id={id}
                    type="number"
                    min={Math.max(1, collected)}
                    step="1"
                    value={value}
                    disabled={disabled}
                    aria-invalid={Boolean(error)}
                    aria-describedby={`${id}-hint`}
                    onChange={event => onChange(event.target.value)}
                />
                <span id={`${id}-hint`} className="fundraising-hint">
                    {collected > 0
                        ? `Уже собрано ${collected.toLocaleString("ru-RU")} ₽. Цель можно увеличить.`
                        : "Когда цель будет достигнута, подарок будет забронирован."}
                </span>
            </>}
            {error && <p className="gift-form-error" role="alert">{error}</p>}
        </div>
    )
}

export default FundraisingGoalInput
