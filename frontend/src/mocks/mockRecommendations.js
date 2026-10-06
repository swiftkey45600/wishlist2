const recommendations = [
    { id: "mock-book", title: "Книга", price: 1200, description: "Новая история для уютного вечера." },
    { id: "mock-game", title: "Настольная игра", price: 2500, description: "Для встреч с друзьями." },
    { id: "mock-mug", title: "Термокружка", price: 1800, description: "Чтобы любимый напиток оставался тёплым." }
]

export async function fetchMockRecommendations() {
    await new Promise(resolve => setTimeout(resolve, 300))
    return recommendations.map(item => ({ ...item }))
}
