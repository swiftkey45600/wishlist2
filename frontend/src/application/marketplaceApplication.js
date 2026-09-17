import { fetchMarketplaces } from "../repositories/marketplaceRepository"

export async function getMarketplaces() {
    try {
        return await fetchMarketplaces()
    } catch (error) {
        console.error(error)
        return []
    }
}
