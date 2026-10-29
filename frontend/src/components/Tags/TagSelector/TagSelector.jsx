import { forwardRef, useImperativeHandle, useRef, useState } from "react"
import { createTag, deleteTag } from "../../../application/tagApplication"
import "./TagSelector.css"

const TagSelector = forwardRef(function TagSelector({ eventId, tags, selectedTagIds, onTagsChange, onChange, disabled = false }, ref) {
    const [newTagName, setNewTagName] = useState("")
    const [error, setError] = useState("")
    const [isCreating, setIsCreating] = useState(false)
    const [deletingTagId, setDeletingTagId] = useState(null)

    function toggleTag(tagId) {
        const nextTagIds = selectedTagIds.includes(tagId)
            ? selectedTagIds.filter(id => id !== tagId)
            : [...selectedTagIds, tagId]

        onChange(nextTagIds)
    }

    const pendingCreate = useRef(null)

    function createPendingTag() {
        if (pendingCreate.current) return pendingCreate.current
        const name = newTagName.trim()
        if (!name) return Promise.resolve(selectedTagIds)
        if (disabled || deletingTagId !== null) return Promise.reject(new Error("Теги пока недоступны"))
        const existing = tags.find(tag => tag.name.trim().toLowerCase() === name.toLowerCase())
        if (existing) {
            const ids = selectedTagIds.includes(existing.id) ? selectedTagIds : [...selectedTagIds, existing.id]
            onChange(ids)
            setNewTagName("")
            setError("")
            return Promise.resolve(ids)
        }
        setError("")
        setIsCreating(true)
        const request = createTag(eventId, name).then(createdTag => {
            const ids = [...selectedTagIds, createdTag.id]
            onTagsChange([...tags, createdTag])
            onChange(ids)
            setNewTagName("")
            return ids
        }).catch(requestError => {
            setError(requestError.response?.status === 409
                ? "Такой тег уже существует. Обновите список тегов."
                : "Не удалось создать тег. Попробуйте ещё раз.")
            throw requestError
        }).finally(() => {
            pendingCreate.current = null
            setIsCreating(false)
        })
        pendingCreate.current = request
        return request
    }

    useImperativeHandle(ref, () => ({ createPendingTag }))

    async function handleDeleteTag(tagId) {
        if (deletingTagId !== null || isCreating || disabled) return

        setError("")
        setDeletingTagId(tagId)
        try {
            await deleteTag(eventId, tagId)
            onTagsChange(tags.filter(tag => tag.id !== tagId))
            onChange(selectedTagIds.filter(id => id !== tagId))
        } catch {
            setError("Не удалось удалить тег. Попробуйте ещё раз.")
        } finally {
            setDeletingTagId(null)
        }
    }

    function handleKeyDown(event) {
        if (event.key === "Enter") {
            event.preventDefault()
            createPendingTag().catch(() => {})
        }
    }

    return (
        <div className="tag-selector">
            <span className="tag-selector-label">Теги</span>

            <div className="tag-selector-list">
                {tags.map(tag => (
                    <span className="tag-selector-item" key={tag.id}>
                        <button
                            type="button"
                            className={`tag-selector-chip ${selectedTagIds.includes(tag.id) ? "selected" : ""}`}
                            disabled={disabled || isCreating || deletingTagId !== null}
                            aria-pressed={selectedTagIds.includes(tag.id)}
                            onClick={() => toggleTag(tag.id)}
                        >
                            {tag.name}
                        </button>
                        <button
                            type="button"
                            className="tag-selector-delete"
                            aria-label={`Удалить тег «${tag.name}»`}
                            title={`Удалить тег «${tag.name}»`}
                            disabled={disabled || isCreating || deletingTagId !== null}
                            onClick={() => handleDeleteTag(tag.id)}
                        >
                            ×
                        </button>
                    </span>
                ))}
                {tags.length === 0 && (
                    <span className="tag-selector-empty">Тегов пока нет</span>
                )}
            </div>

            <div className="tag-create-row">
                <input
                    disabled={disabled || isCreating || deletingTagId !== null}
                    value={newTagName}
                    onChange={event => setNewTagName(event.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Введите тег и нажмите Enter"
                    maxLength={40}
                />
            </div>

            {error && <span className="tag-selector-error" role="alert">{error}</span>}
        </div>
    )
})

export default TagSelector
