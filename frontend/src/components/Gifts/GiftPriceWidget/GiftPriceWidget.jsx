import { useEffect, useState } from "react"
import { getEventStatistics } from "../../../application/eventApplication"
import "./GiftPriceWidget.css"

function GiftPriceWidget({ eventId, refreshKey }) {
    const [statistics, setStatistics] = useState(null)
    const [isLoading, setIsLoading] = useState(true)
    const [hasError, setHasError] = useState(false)

    useEffect(() => {
        let isCurrentRequest = true

        async function loadStatistics() {
            setIsLoading(true)
            setHasError(false)

            const data = await getEventStatistics(eventId)
            if (!isCurrentRequest) return

            if (data) {
                setStatistics(data)
            } else {
                setStatistics(null)
                setHasError(true)
            }
            setIsLoading(false)
        }

        loadStatistics()
        return () => {
            isCurrentRequest = false
        }
    }, [eventId, refreshKey])

    const priceRanges = statistics?.price_ranges || []
    const largestRange = Math.max(1, ...priceRanges.map((range) => range.count))

    return (
        <section className="gift-price-widget" aria-labelledby="gift-price-widget-title">
            <header className="gift-price-widget-header">
                <div>
                    <h2 id="gift-price-widget-title">Цены подарков</h2>
                    {!isLoading && !hasError && statistics && (
                        <p>{statistics.total_gifts} подарков в событии</p>
                    )}
                </div>
            </header>

            {isLoading && <p className="gift-price-widget-message">Загружаем статистику...</p>}
            {!isLoading && hasError && (
                <p className="gift-price-widget-message error">Не удалось загрузить статистику.</p>
            )}

            {!isLoading && !hasError && statistics && (
                <div className="gift-price-widget-content">
                    <div className="gift-price-chart" aria-label="Количество подарков по диапазонам цен">
                        {priceRanges.map((range) => (
                            <div className="gift-price-column" key={range.key}>
                                <div className="gift-price-bar-track">
                                    <span
                                        className="gift-price-bar"
                                        style={{ height: `${(range.count / largestRange) * 100}%` }}
                                    />
                                </div>
                                <strong>{range.count}</strong>
                                <span className="gift-price-label">{range.label}</span>
                            </div>
                        ))}
                    </div>

                    <div className="gift-price-recommendations">
                        <h3>Рекомендации</h3>
                        {statistics.recommendations?.length ? (
                            <ul>
                                {statistics.recommendations.map((recommendation) => (
                                    <li key={recommendation}>{recommendation}</li>
                                ))}
                            </ul>
                        ) : (
                            <p>Распределение подарков по ценовым диапазонам сбалансировано.</p>
                        )}
                    </div>
                </div>
            )}
        </section>
    )
}

export default GiftPriceWidget