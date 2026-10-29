import assert from "node:assert/strict"
import test from "node:test"
import { archiveDay, getEventDurationDays, isValidDuration } from "../src/utils/eventDuration.js"

test("duration uses calendar days across month, leap day and daylight saving boundaries", () => {
    assert.equal(getEventDurationDays("2028-02-28T12:00", "2028-03-01T23:59"), 3)
    assert.equal(getEventDurationDays("2026-03-07T12:00", "2026-03-09T23:59"), 3)
    assert.equal(archiveDay("2099-12-31T15:00", 3).toISOString().slice(0, 10), "2100-01-03")
    assert.equal(archiveDay("2028-02-28T12:00", 2).toISOString().slice(0, 10), "2028-03-01")
    assert.equal(archiveDay(null, 3), null)
    assert.equal(archiveDay("2099-01-01", 0), null)
    assert.equal(isValidDuration(1.5), false)
    assert.equal(isValidDuration(3650), true)
})
