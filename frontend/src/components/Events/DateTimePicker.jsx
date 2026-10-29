/** Use the browser calendar and time selector instead of typed dates. */
function DateTimePicker({ value, onChange, min, onBlur }) {
    function openPicker(event) {
        try { event.currentTarget.showPicker?.() } catch { /* Browser may open the native picker itself. */ }
    }

    function handleKeyDown(event) {
        if (event.key === "Tab") return
        if (event.key === "Enter" || event.key === " ") openPicker(event)
        event.preventDefault()
    }

    return <input type="datetime-local" value={value} min={min} onChange={onChange} onBlur={onBlur}
        onClick={openPicker} onKeyDown={handleKeyDown} onPaste={event => event.preventDefault()}
        onDrop={event => event.preventDefault()} inputMode="none" />
}
export default DateTimePicker
