import assert from "node:assert/strict"
import test from "node:test"
import process from "node:process"
import { isPastEventDate, todayLocalDate, currentLocalTime } from "../src/utils/eventDate.js"

test("event date validation uses the user's local date and minute", () => {
    const now = new Date(2026, 9, 30, 15, 42, 30)
    assert.equal(todayLocalDate(now), "2026-10-30")
    assert.equal(currentLocalTime(now), "15:42")
    assert.equal(isPastEventDate("2026-10-30T15:41", now), true)
    assert.equal(isPastEventDate("2026-10-30T15:42", now), false)
    assert.equal(isPastEventDate("2026-10-30T15:43", now), false)
    assert.equal(isPastEventDate("2026-10-29T23:59", now), true)
    assert.equal(isPastEventDate("2026-10-31T00:00", now), false)
    assert.equal(isPastEventDate("", now), false)
})

test("local event time carries its offset and represents the same moment", async () => {
    const { execFileSync } = await import("node:child_process")
    const script = `import { withLocalOffset } from './src/utils/eventDate.js'; console.log(withLocalOffset('2099-11-01T15:00'))`
    const petersburg = execFileSync(process.execPath, ["--input-type=module", "-e", script], { env: { ...process.env, TZ: "Europe/Moscow" }, encoding: "utf8" }).trim()
    assert.equal(petersburg, "2099-11-01T15:00+03:00")
    const kaliningrad = new Intl.DateTimeFormat("ru-RU", { timeZone: "Europe/Kaliningrad", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).format(new Date(petersburg))
    assert.equal(kaliningrad, "14:00")
})
