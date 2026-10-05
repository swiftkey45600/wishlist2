import api from "../services/api"

export async function parseMarketplaceProduct(url) {
    const response = await api.post("/marketplace/parse", { url })
    return response.data
}
