import { useState } from "react"
import { createTag, deleteTag } from "../../../application/tagApplication"
import "./TagSelector.css"

function TagSelector({ eventId, tags, selectedTagIds, onTagsChange, onChange, disabled = false }) {
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

    async function handleCreateTag() {
        if (isCreating || deletingTagId !== null || disabled) return
        const name = newTagName.trim()

        if (!name) {
            setError("Введите название тега")
            return
        }

        if (tags.some(tag => tag.name.toLowerCase() === name.toLowerCase())) {
            setError("Такой тег уже существует")
            return
        }

        setError("")
        setIsCreating(true)
        try {
            const createdTag = await createTag(eventId, name)
            onTagsChange([...tags, createdTag])
            onChange([...selectedTagIds, createdTag.id])
            setNewTagName("")
        } catch (requestError) {
            setError(requestError.response?.status === 409
                ? "Такой тег уже существует. Обновите список тегов."
                : "Не удалось создать тег. Попробуйте ещё раз.")
        } finally {
            setIsCreating(false)
        }
    }

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
            handleCreateTag()
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
                    placeholder="Новый тег"
                    maxLength={40}
                />
                <button
                    type="button"
                    className="tag-create-button"
                    onClick={handleCreateTag}
                    disabled={disabled || isCreating || deletingTagId !== null}
                >
                    {isCreating ? "Создаём..." : "+ Создать"}
                </button>
            </div>

            {error && <span className="tag-selector-error" role="alert">{error}</span>}
        </div>
    )
}

export default TagSelector
