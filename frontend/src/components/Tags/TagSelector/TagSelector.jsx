import { useState } from "react"
import { createTag } from "../../../application/tagApplication"
import "./TagSelector.css"

function TagSelector({ eventId, tags, selectedTagIds, onTagsChange, onChange }) {
    const [newTagName, setNewTagName] = useState("")
    const [error, setError] = useState("")
    const [isCreating, setIsCreating] = useState(false)

    function toggleTag(tagId) {
        const nextTagIds = selectedTagIds.includes(tagId)
            ? selectedTagIds.filter(id => id !== tagId)
            : [...selectedTagIds, tagId]

        onChange(nextTagIds)
    }

    async function handleCreateTag() {
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
        const createdTag = await createTag(eventId, name)
        setIsCreating(false)

        if (!createdTag) {
            setError("Не удалось создать тег")
            return
        }

        onTagsChange([...tags, createdTag])
        onChange([...selectedTagIds, createdTag.id])
        setNewTagName("")
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
                    <button
                        key={tag.id}
                        type="button"
                        className={`tag-selector-chip ${selectedTagIds.includes(tag.id) ? "selected" : ""}`}
                        onClick={() => toggleTag(tag.id)}
                    >
                        {tag.name}
                    </button>
                ))}
                {tags.length === 0 && (
                    <span className="tag-selector-empty">Тегов пока нет</span>
                )}
            </div>

            <div className="tag-create-row">
                <input
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
                    disabled={isCreating}
                >
                    {isCreating ? "Создаём..." : "+ Создать"}
                </button>
            </div>

            {error && <span className="tag-selector-error">{error}</span>}
        </div>
    )
}

export default TagSelector
