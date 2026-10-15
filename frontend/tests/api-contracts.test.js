import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import test from "node:test"
import vm from "node:vm"

async function loadApplication(name, api, createGift = () => {}) {
    const context = vm.createContext({ Error })
    const apiModule = new vm.SyntheticModule(["default"], function () {
        this.setExport("default", api)
    }, { context })
    const giftModule = new vm.SyntheticModule(["createGift"], function () {
        this.setExport("createGift", createGift)
    }, { context })
    const source = await readFile(new URL(`../src/application/${name}.js`, import.meta.url), "utf8")
    const module = new vm.SourceTextModule(source, {
        context,
        initializeImportMeta(meta) { meta.env = { DEV: false } }
    })
    await module.link(specifier => specifier.includes("services/api") ? apiModule : giftModule)
    await module.evaluate()
    return module.namespace
}

test("guest reservation uses real API and preserves gift fields", async () => {
    const calls = []
    const application = await loadApplication("guestReservationApplication", {
        async post(path, body) {
            calls.push({ path, body })
            return { data: { id: 42 } }
        }
    })
    const gift = { id: 7, title: "Book", status: "available", tags: [{ id: 3 }] }
    const result = await application.changeGuestReservation("public-token", gift, { name: " Guest ", secretWord: " word " })
    assert.equal(calls[0].path, "/events/public/public-token/gifts/7/reservation")
    assert.equal(calls[0].body.name, "Guest")
    assert.equal(calls[0].body.secret_word, " word ")
    assert.equal(result.reservation_id, 42)
    assert.equal(result.status, "reserved")
    assert.equal(result.tags, gift.tags)
    assert.equal(gift.status, "available")
})

test("guest cancellation sends the secret word in the DELETE body", async () => {
    let request
    const application = await loadApplication("guestReservationApplication", {
        async delete(path, config) { request = { path, config } }
    })
    const result = await application.changeGuestReservation("token", { id: 7, status: "reserved", reservation_id: 42 }, { secretWord: "snow" })
    assert.equal(request.config.data.secret_word, "snow")
    assert.equal(result.status, "available")
    assert.equal(result.reservation_id, null)
})

test("API conflicts and wrong words remain failures", async () => {
    for (const status of [403, 409, 429]) {
        const application = await loadApplication("guestReservationApplication", {
            async post() { throw { response: { status } } }
        })
        await assert.rejects(application.changeGuestReservation("token", { id: 7, status: "available" }, { name: "Guest", secretWord: "snow" }))
    }
})

test("recommendations load from the owner's event endpoint", async () => {
    const items = [{ id: 1, title: "Book", price: 100 }]
    const application = await loadApplication("recommendationApplication", {
        async get(path) {
            assert.equal(path, "/events/12/recommendations")
            return { data: items }
        }
    })
    assert.equal(await application.getRecommendations(12), items)
})

test("adding a recommendation copies only product data", async () => {
    let body
    const application = await loadApplication("recommendationApplication", {}, async data => {
        body = data
        return { ...data, id: 99 }
    })
    const result = await application.addRecommendedGift(12, {
        id: 1, event_id: 777, title: "Book", price: 100,
        status: "reserved", reservation_id: 42, tags: [{ id: 9 }], public_token: "private"
    })
    assert.equal(result.id, 99)
    assert.equal(body.event_id, 12)
    assert.equal(body.status, "available")
    for (const key of ["id", "reservation_id", "tags", "public_token"]) assert.equal(key in body, false)
})
