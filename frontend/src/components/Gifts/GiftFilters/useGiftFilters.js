import { useSearchParams } from "react-router-dom"

function getNonNegativeNumber(value) {
    if (value === "" || value === null) return null
    const number = Number(value)
    return Number.isFinite(number) && number >= 0 ? number : null
}

export function useGiftFilters(gifts) {
    const [searchParams, setSearchParams] = useSearchParams()
    const filters = {
        search: searchParams.get("q") || searchParams.get("giftSearch") || "",
        status: searchParams.get("status") || searchParams.get("giftStatus") || "",
        tagIds: searchParams.getAll("tags").length
            ? searchParams.getAll("tags").slice(0, 1)
            : searchParams.get("giftTag")
                ? [searchParams.get("giftTag")]
                : [],
        minPrice: searchParams.get("min_price") || "",
        maxPrice: searchParams.get("max_price") || "",
        sortBy: searchParams.get("sort_by") || "id",
        sortOrder: searchParams.get("sort_order") || "asc",
    }
    const search = filters.search.trim().toLocaleLowerCase("ru")
    const minPrice = getNonNegativeNumber(filters.minPrice)
    const maxPrice = getNonNegativeNumber(filters.maxPrice)
    const filteredGifts = gifts.filter((gift) => {
        const searchableText = `${gift.title || ""} ${gift.description || ""}`.toLocaleLowerCase("ru")
        const matchesSearch = !search || searchableText.includes(search)
        const matchesStatus = !filters.status || gift.status === filters.status
        const matchesTag = !filters.tagIds.length
            || filters.tagIds.some((tagId) => tagId === "untagged"
                ? !gift.tags?.length
                : gift.tags?.some((tag) => String(tag.id) === tagId))
        const price = Number(gift.price)
        const matchesMinPrice = minPrice === null || price >= minPrice
        const matchesMaxPrice = maxPrice === null || price <= maxPrice

        return matchesSearch && matchesStatus && matchesTag && matchesMinPrice && matchesMaxPrice
    })
    const sortedGifts = [...filteredGifts].sort((left, right) => {
        const comparison = filters.sortBy === "price"
            ? Number(left.price) - Number(right.price)
            : filters.sortBy === "title"
                ? (left.title || "").localeCompare(right.title || "", "ru")
                : Number(left.id) - Number(right.id)
        return filters.sortOrder === "desc" ? -comparison : comparison
    })

    function updateFilter(key, value) {
        const paramName = {
            search: "q",
            status: "status",
            tagIds: "tags",
            minPrice: "min_price",
            maxPrice: "max_price",
            sortBy: "sort_by",
            sortOrder: "sort_order",
        }[key]

        setSearchParams((currentParams) => {
            const nextParams = new URLSearchParams(currentParams)
            nextParams.delete("giftSearch")
            nextParams.delete("giftStatus")
            nextParams.delete("giftTag")
            if (key === "sort") {
                nextParams.set("sort_by", value.sortBy)
                nextParams.set("sort_order", value.sortOrder)
                return nextParams
            }
            nextParams.delete(paramName)
            if (Array.isArray(value)) {
                value.forEach((item) => nextParams.append(paramName, item))
            } else if (value) {
                nextParams.set(paramName, value)
            }
            return nextParams
        }, { replace: true })
    }

    return {
        filters,
        filteredGifts: sortedGifts,
        updateFilter,
    }
}