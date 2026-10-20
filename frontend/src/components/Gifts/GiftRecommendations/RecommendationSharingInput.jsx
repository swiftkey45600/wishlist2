import { useId } from "react"
import "./RecommendationSharingInput.css"

function RecommendationSharingInput({ checked, onChange, disabled = false }) {
    const id = useId()
    return (
        <div className="recommendation-sharing">
            <label>
                <input type="checkbox" checked={checked} disabled={disabled} aria-describedby={id}
                    onChange={event => onChange(event.target.checked)} />
                Показывать подарок в общих рекомендациях
            </label>
            <span id={id}>
                Будут видны название, цена, изображение и ссылка на товар. Данные события и взносы останутся скрытыми.
            </span>
        </div>
    )
}

export default RecommendationSharingInput
