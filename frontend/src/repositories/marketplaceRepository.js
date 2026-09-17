import api from "../services/api"

export async function fetchMarketplaces() {
    const response = await api.get("/marketplaces")
    return response.data
}
