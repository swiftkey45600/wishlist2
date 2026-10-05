import "./GiftEditForm.css"
import { useEffect, useRef, useState } from "react"
import { getImage, resolveImageUrl, uploadImageFile } from "../../../application/imageApplication"
import { parseMarketplaceProduct } from "../../../application/marketplaceApplication"
import TagSelector from "../../Tags/TagSelector/TagSelector"

const ALLOWED_IMAGE_TYPES = new Set(["image/jpeg", "image/png", "image/webp", "image/gif"])

function GiftEditForm({ gift, tags, onTagsChange, onChange, onSave, onCancel }) {
    const [error, setError] = useState("")
    const [isSaving, setIsSaving] = useState(false)
    const [isParsingMarketplace, setIsParsingMarketplace] = useState(false)
    const [imageFile, setImageFile] = useState(null)
    const imageInputRef = useRef(null)
    const [imagePreview, setImagePreview] = useState(
        resolveImageUrl(gift.image_id, gift.picture_url || gift.image_url)
    )

    useEffect(() => {
        if (!imagePreview.startsWith("blob:")) return
        return () => URL.revokeObjectURL(imagePreview)
    }, [imagePreview])

    useEffect(() => {
        if (imageFile || !gift.image_id) return

        let cancelled = false
        getImage(gift.image_id).then((imageBlob) => {
            if (!cancelled && imageBlob) {
                setImagePreview(URL.createObjectURL(imageBlob))
            }
        })

        return () => {
            cancelled = true
        }
    }, [imageFile, gift.image_id])

    async function handleMarketplaceAutofill() {
        const url = gift.marketplace_url?.trim()
        if (!url) {
            setError("Вставьте ссылку на товар")
            return
        }

        setError("")
        setIsParsingMarketplace(true)
        try {
            const { product, error: parseError } = await parseMarketplaceProduct(url)
            if (!product) {
                setError(parseError)
                return
            }

            setImageFile(null)
            if (imageInputRef.current) imageInputRef.current.value = ""
            setImagePreview(resolveImageUrl(product.image_id, product.picture_url))
            onChange({
                ...gift,
                title: product.title || gift.title,
                price: product.price ?? gift.price,
                image_id: product.image_id,
                picture_url: product.image_id ? null : resolveImageUrl(null, product.picture_url),
                marketplace_url: product.marketplace_url || url
            })
        } finally {
            setIsParsingMarketplace(false)
        }
    }

    async function handleSubmit(event) {
        event.preventDefault()

        if (!gift.title?.trim()) {
            setError("Введите название подарка")
            return
        }

        const price = Number(gift.price)
        if (!gift.price || Number.isNaN(price) || price <= 0) {
            setError("Цена должна быть положительным числом")
            return
        }

        setError("")
        setIsSaving(true)
        try {
            let imageId = gift.image_id
            if (imageFile) {
                const uploadedImage = await uploadImageFile(imageFile)
                if (!uploadedImage?.id) {
                    setError("Не удалось загрузить изображение")
                    return
                }
                imageId = uploadedImage.id
            }

            const saved = await onSave(imageId)
            if (!saved) setError("Не удалось сохранить подарок")
        } finally {
            setIsSaving(false)
        }
    }

    return (
        <form
            className="gift-edit-form"
            onSubmit={handleSubmit}
        >
            <h3>Редактирование подарка</h3>

            <label>
                Название
                <input
                    value={gift.title || ""}
                    onChange={e =>
                        onChange({
                            ...gift,
                            title: e.target.value
                        })
                    }
                />
            </label>

            <label>
                Цена
                <input
                    type="number"
                    value={gift.price || ""}
                    onChange={e =>
                        onChange({
                            ...gift,
                            price: e.target.value
                        })
                    }
                />
            </label>

            <label>
                Описание
                <textarea
                    value={gift.description || ""}
                    onChange={e =>
                        onChange({
                            ...gift,
                            description: e.target.value
                        })
                    }
                />
            </label>

            <label>
                Загрузить изображение файлом
                <input
                    ref={imageInputRef}
                    disabled={isSaving || isParsingMarketplace}
                    type="file"
                    accept="image/jpeg,image/png,image/webp,image/gif"
                    onChange={(event) => {
                        const file = event.target.files?.[0] || null
                        if (!file) return
                        if (!ALLOWED_IMAGE_TYPES.has(file.type)) {
                            setError("Выберите изображение в формате JPEG, PNG, WebP или GIF")
                            event.target.value = ""
                            return
                        }
                        setError("")
                        setImageFile(file)
                        setImagePreview(file
                            ? URL.createObjectURL(file)
                            : resolveImageUrl(gift.image_id, gift.picture_url || gift.image_url))
                    }}
                />
            </label>
            <label>
                Или указать ссылку на изображение
                <input
                    type="url"
                    pattern="https?://.+"
                    placeholder="https://example.com/photo.jpg"
                    value={imageFile || gift.image_id ? "" : gift.picture_url || ""}
                    disabled={isSaving || isParsingMarketplace}
                    onChange={event => {
                        const url = event.target.value
                        setImageFile(null)
                        if (imageInputRef.current) imageInputRef.current.value = ""
                        setError("")
                        setImagePreview(/^https?:\/\//i.test(url.trim()) ? url.trim() : "")
                        onChange({ ...gift, image_id: null, image_url: null, picture_url: url })
                    }}
                />
            </label>
            {imagePreview && <img className="gift-image-preview" src={imagePreview} alt="Предпросмотр подарка" />}

            <div className="marketplace-autofill">
                <label>
                    Ссылка на маркетплейс
                    <input
                        value={gift.marketplace_url || ""}
                        onChange={e =>
                            onChange({
                                ...gift,
                                marketplace_url: e.target.value
                            })
                        }
                    />
                </label>
                <button
                    type="button"
                    onClick={handleMarketplaceAutofill}
                    disabled={isParsingMarketplace || isSaving}
                >
                    {isParsingMarketplace ? "Заполняем..." : "Заполнить по ссылке"}
                </button>
            </div>

            {tags && <TagSelector
                eventId={gift.event_id}
                tags={tags}
                selectedTagIds={gift.tag_ids || []}
                onTagsChange={onTagsChange}
                onChange={tagIds => onChange({ ...gift, tag_ids: tagIds })}
            />}

            {error && <p className="gift-edit-error">{error}</p>}

            <div className="gift-edit-actions">
                <button type="button" onClick={onCancel} disabled={isSaving || isParsingMarketplace}>
                    Отмена
                </button>
                <button type="submit" disabled={isSaving || isParsingMarketplace}>
                    {isSaving ? "Сохранение..." : "Сохранить"}
                </button>
            </div>
        </form>
    )
}

export default GiftEditForm
