import assert from "node:assert/strict"
import test from "node:test"
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
