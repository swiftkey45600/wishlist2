import { useEffect, useRef, useState } from "react"
import { createPortal } from "react-dom"
import "leaflet/dist/leaflet.css"
import "./LocationPicker.css"
import { getLocationCoordinates, withoutLocationCoordinates } from "./location"

function LocationPicker({ value, onChange }) {
    const [open, setOpen] = useState(false)
    const [point, setPoint] = useState(null)
    const [mapError, setMapError] = useState(false)
    const mapElement = useRef(null)
    useEffect(() => {
        if (!open || !mapElement.current) return
        const initial = getLocationCoordinates(value)
        let map
        let active = true
        import("leaflet").then(module => {
            if (!active || !mapElement.current) return
            const L = module.default
            map = L.map(mapElement.current).setView(initial || [55.7558, 37.6173], initial ? 14 : 4)
            map.attributionControl.setPrefix('<a href="https://leafletjs.com">Leaflet</a>')
            let loadedTiles = 0
            const tiles = L.tileLayer(import.meta.env.VITE_MAP_TILE_URL || "https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
                maxZoom: 19,
                referrerPolicy: "strict-origin-when-cross-origin",
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                updateWhenIdle: true,
                keepBuffer: 1
            })
            tiles.on("tileload", () => { loadedTiles += 1; if (active) setMapError(false) })
            tiles.on("load", () => { if (active) setMapError(loadedTiles === 0) })
            tiles.addTo(map)
            const marker = L.circleMarker(initial || [0, 0], { radius: 8, color: "#fff", weight: 3, fillColor: "#7152df", fillOpacity: 1 })
            if (initial) marker.addTo(map)
            map.on("click", event => { marker.setLatLng(event.latlng).addTo(map); setPoint([event.latlng.lat, event.latlng.lng]) })
        }).catch(() => { if (active) setMapError(true) })
        return () => { active = false; map?.remove() }
    }, [open, value])

    function showMap() { setMapError(false); setPoint(getLocationCoordinates(value)); setOpen(true) }
    function save() {
        if (!point) return
        const name = withoutLocationCoordinates(value)
        onChange(`${name || "Точка на карте"} (координаты: ${point[0].toFixed(5)}, ${point[1].toFixed(5)})`)
        setOpen(false)
    }

    return <div className="location-picker">
        <label className="create-event-field">Место<input value={value} onChange={event => onChange(event.target.value)} placeholder="Город или место" /></label>
        <button type="button" className="location-map-button" onClick={showMap}>Выбрать на карте</button>
        {open && createPortal(<div className="location-overlay" onClick={event => { if (event.target === event.currentTarget) setOpen(false) }}>
            <div className="location-dialog" role="dialog" aria-modal="true" aria-labelledby="location-title">
                <h3 id="location-title">Выберите место</h3>
                <p>Нажмите на карту, чтобы поставить точку. Название места можно вписать вручную.</p>
                <div className="location-map" ref={mapElement} aria-label="Карта для выбора места" />
                {mapError && <p role="alert">Не удалось загрузить карту. Проверьте подключение или укажите место вручную.</p>}
                <div className="location-actions"><button type="button" onClick={() => setOpen(false)}>Отмена</button><button type="button" disabled={!point} onClick={save}>Выбрать точку</button></div>
            </div>
        </div>, document.body)}
    </div>
}
export default LocationPicker
