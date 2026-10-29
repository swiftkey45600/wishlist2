import "./SegmentedControl.css"

/** A single moving surface, shared by every section switcher. */
export default function SegmentedControl({ label, options, value, onChange }) {
    const index = Math.max(0, options.findIndex(option => option.value === value))
    function handleKeyDown(event) {
        if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return
        event.preventDefault()
        const next = event.key === "Home" ? 0 : event.key === "End" ? options.length - 1
            : (index + (event.key === "ArrowRight" ? 1 : -1) + options.length) % options.length
        onChange(options[next].value)
        event.currentTarget.querySelectorAll("button")[next].focus()
    }
    return <div className="segmented-control" role="group" aria-label={label}
        style={{ "--segments": options.length, "--selected": index }} onKeyDown={handleKeyDown}>
        <span className="segmented-control-indicator" aria-hidden="true" />
        {options.map(option => <button key={String(option.value)} type="button"
            aria-pressed={option.value === value} onClick={() => onChange(option.value)}>{option.label}</button>)}
    </div>
}
