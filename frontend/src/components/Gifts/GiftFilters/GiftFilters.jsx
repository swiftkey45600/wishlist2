import "./GiftFilters.css"

const statusOptions = [
    ["available", "Свободные"],
    ["reserved", "Забронированные"],
    ["bought", "Купленные"],
]

function GiftFilters({ tags, filters, onFilterChange, hideStatus = false }) {
    return (
        <div className="gift-filter-panel">
            <label className="gift-filter-field gift-filter-search">
                <span>Поиск</span>
                <input
                    type="search"
                    value={filters.search}
                    onChange={(event) => onFilterChange("search", event.target.value)}
                    placeholder="Название или описание"
                />
            </label>

            <div className="gift-filters" aria-label="Фильтры подарков">
                {!hideStatus && <label className="gift-filter-field">
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
                </label>}

                <label className="gift-filter-field">
                    <span>Тег</span>
                    <select
                        value={filters.tagIds[0] || ""}
                        onChange={(event) => onFilterChange(
                            "tagIds",
                            event.target.value ? [event.target.value] : []
                        )}
                    >
                        <option value="">Все теги</option>
                        <option value="untagged">Без тегов</option>
                        {tags.map((tag) => (
                            <option key={tag.id} value={tag.id}>{tag.name}</option>
                        ))}
                    </select>
                </label>

                <fieldset className="gift-price-filter">
                    <legend>Цена</legend>
                    <label className="gift-filter-field">
                        <input
                            type="number"
                            min="0"
                            value={filters.minPrice}
                            onChange={(event) => onFilterChange("minPrice", event.target.value)}
                            placeholder="От"
                            aria-label="Цена от"
                        />
                    </label>
                    <label className="gift-filter-field">
                        <input
                            type="number"
                            min="0"
                            value={filters.maxPrice}
                            onChange={(event) => onFilterChange("maxPrice", event.target.value)}
                            placeholder="До"
                            aria-label="Цена до"
                        />
                    </label>
                </fieldset>

                <label className="gift-filter-field">
                    <span>Сортировка</span>
                    <select
                        value={`${filters.sortBy}:${filters.sortOrder}`}
                        onChange={(event) => {
                            const [sortBy, sortOrder] = event.target.value.split(":")
                            onFilterChange("sort", { sortBy, sortOrder })
                        }}
                    >
                        <option value="id:asc">Добавление — по возрастанию</option>
                        <option value="id:desc">Добавление — по убыванию</option>
                        <option value="price:asc">Цена — по возрастанию</option>
                        <option value="price:desc">Цена — по убыванию</option>
                        <option value="title:asc">Название — по возрастанию</option>
                        <option value="title:desc">Название — по убыванию</option>
                        <option value="priority:desc">Сначала самые желанные</option>
                    </select>
                </label>
            </div>
        </div>
    )
}

export default GiftFilters
