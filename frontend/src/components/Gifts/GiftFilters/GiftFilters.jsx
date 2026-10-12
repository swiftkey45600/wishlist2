import "./GiftFilters.css"

const statusOptions = [
    ["available", "Свободные"],
    ["reserved", "Забронированные"],
    ["bought", "Купленные"],
]

function GiftFilters({ tags, filters, onFilterChange }) {
    return (
        <div className="gift-filters" aria-label="Фильтры подарков">
            <label className="gift-filter-field gift-filter-search">
                <span>Поиск</span>
                <input
                    type="search"
                    value={filters.search}
                    onChange={(event) => onFilterChange("search", event.target.value)}
                    placeholder="Название или описание"
                />
            </label>

            <label className="gift-filter-field">
                <span>Статус</span>
                <select
                    value={filters.status}
                    onChange={(event) => onFilterChange("status", event.target.value)}
                >
                    <option value="">Все статусы</option>
                    {statusOptions.map(([value, label]) => (
                        <option key={value} value={value}>{label}</option>
                    ))}
                </select>
            </label>

            <label className="gift-filter-field">
                <span>Тег</span>
                <select
                    value={filters.tagId}
                    onChange={(event) => onFilterChange("tagId", event.target.value)}
                >
                    <option value="">Все теги</option>
                    <option value="untagged">Без тегов</option>
                    {tags.map((tag) => (
                        <option key={tag.id} value={tag.id}>{tag.name}</option>
                    ))}
                </select>
            </label>

        </div>
    )
}

export default GiftFilters