import assert from "node:assert/strict"
import test from "node:test"
import { uniquePersonalGifts } from "../src/utils/personalGifts.js"

test("event imports appear once with their source, including chained imports", () => {
    const wish = { id: 1, isPersonal: true, title: "Book" }
    const copy = { id: 2, source_wish_id: 1, title: "Book" }
    const next = { id: 3, source_gift_id: 2, title: "Book" }
    const other = { id: 4, title: "Book" }
    assert.deepEqual(uniquePersonalGifts([wish, copy, next, other]), [wish, other])
    assert.deepEqual(uniquePersonalGifts([copy, next]), [copy])
    assert.deepEqual(uniquePersonalGifts([wish, { ...copy, received: true }]), [{ ...copy, received: true }])
    assert.deepEqual(uniquePersonalGifts([other, { ...next, source_gift_id: 4 }]), [other])
})
