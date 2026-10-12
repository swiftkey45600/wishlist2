import { useSearchParams } from "react-router-dom"

export function useGiftFilters(gifts) {
    const [searchParams, setSearchParams] = useSearchParams()
    const filters = {
        search: searchParams.get("giftSearch") || "",
        status: searchParams.get("giftStatus") || "",
        tagId: searchParams.get("giftTag") || "",
    }
    const search = filters.search.trim().toLocaleLowerCase("ru")
    const filteredGifts = gifts.filter((gift) => {
        const searchableText = `${gift.title || ""} ${gift.description || ""}`.toLocaleLowerCase("ru")
        const matchesSearch = !search || searchableText.includes(search)
        const matchesStatus = !filters.status || gift.status === filters.status
        const matchesTag = !filters.tagId
            || (filters.tagId === "untagged"
                ? !gift.tags?.length
                : gift.tags?.some((tag) => String(tag.id) === filters.tagId))

        return matchesSearch && matchesStatus && matchesTag
    })

    function updateFilter(key, value) {
        const paramName = {
            search: "giftSearch",
            status: "giftStatus",
            tagId: "giftTag",
        }[key]

        setSearchParams((currentParams) => {
            const nextParams = new URLSearchParams(currentParams)
            if (value) nextParams.set(paramName, value)
            else nextParams.delete(paramName)
            return nextParams
        }, { replace: true })
    }

    return {
        filters,
        filteredGifts,
        updateFilter,
    }
}