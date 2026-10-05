import { parseMarketplaceProduct as parseMarketplaceProductRepository } from "../repositories/marketplaceRepository"

export async function parseMarketplaceProduct(url) {
    try {
        const parsedUrl = new URL(url)
        if (parsedUrl.hostname.endsWith("market.yandex.ru") && parsedUrl.pathname.startsWith("/showcaptcha")) {
            return {
                product: null,
                error: "Это ссылка на CAPTCHA Яндекс Маркета. Вставьте ссылку на карточку товара"
            }
        }
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
