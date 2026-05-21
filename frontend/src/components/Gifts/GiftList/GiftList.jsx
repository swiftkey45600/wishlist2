import "./GiftList.css"

import GiftCard from "../GiftCard/GiftCard"

function GiftList() {
    const gifts = [
        {
            id:1,
            title:"MacBook",
            price:67000
        },

        {
            id:2,
            title:"AirPods",
            price:52000
        },

        {
            id:3,
            title:"Книга",
            price:100500
        }
    ]

    return (
        <div className="gift-list">
            <div className="gift-list-header">
                <h2>Подарки • 3</h2>

                <button className="add-gift-button">+ Добавить подарок</button>
            </div>

            <div className="gift-grid">
                {
                    gifts.map(gift => (
                        <GiftCard 
                            key={gift.id}
                            gift={gift}
                        />
                    ))
                }
            </div>
        </div>
    )
}

export default GiftList
