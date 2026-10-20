import { parseMarketplaceProduct as parseMarketplaceProductRepository } from "../repositories/marketplaceRepository"

export async function parseMarketplaceProduct(url) {
    try {
        const parsedUrl = new URL(url)
        if (!["http:", "https:"].includes(parsedUrl.protocol)) {
            return { product: null, error: "Вставьте ссылку на товар, начинающуюся с http:// или https://" }
        }
        if (parsedUrl.hostname.endsWith("market.yandex.ru") && parsedUrl.pathname.startsWith("/showcaptcha")) {
            return {
                product: null,
                error: "Это ссылка на CAPTCHA Яндекс Маркета. Вставьте ссылку на карточку товара"
            }
        }
        const product = await parseMarketplaceProductRepository(url)
        return { product, error: null }
    } catch (error) {
        return {
            product: null,
            error: typeof error.response?.data?.detail === "string"
                ? error.response.data.detail
                : "Не удалось получить данные товара. Проверьте ссылку или заполните поля вручную"
        }
    }
}
