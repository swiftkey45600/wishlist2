import { parseMarketplaceProduct as parseMarketplaceProductRepository } from "../repositories/marketplaceRepository"

export async function parseMarketplaceProduct(url) {
    try {
        const product = await parseMarketplaceProductRepository(url)
        return { product, error: null }
    } catch (error) {
        console.error(error)
        return {
            product: null,
            error: error.response?.data?.detail || "Не удалось получить данные товара"
        }
    }
}
