const emojiPool = ["🎁", "🌷", "🍰", "🎧", "📚", "🧸", "🎮", "☕", "✨", "🌿"]

const recommendations = [
    { id: "mock-book", title: "Книга", price: 1200, description: "Бойцовский клуб." },
    { id: "mock-game", title: "GTA VI", price: 5000, description: "Я жду её очень долго." },
    { id: "mock-mug", title: "Плойка", price: 35000, description: "Чтобы играть в гташку." }
].map((item) => ({
    ...item,
    emoji: emojiPool[Math.floor(Math.random() * emojiPool.length)]
}))

export async function fetchMockRecommendations() {
    await new Promise(resolve => setTimeout(resolve, 300))
    return recommendations.map(item => ({ ...item }))
}
