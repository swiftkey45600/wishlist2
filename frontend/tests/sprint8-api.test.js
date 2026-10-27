import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import test from "node:test"
import vm from "node:vm"

test("archive controls are disabled until the backend is connected", async () => {
    const calls = []
    const api = {
        patch: async (path, body) => { calls.push([path, body]); return { data: { event: { id: 12, status: "archived" } } } },
        post: async (path, body) => { calls.push([path, body]); return { data: { event: { id: 13 } } } }
    }
    const context = vm.createContext({})
    const dependency = new vm.SyntheticModule(["default"], function () { this.setExport("default", api) }, { context })
    const source = await readFile(new URL("../src/repositories/eventArchiveRepository.js", import.meta.url), "utf8")
    const module = new vm.SourceTextModule(source, { context, initializeImportMeta(meta) { meta.env = {} } })
    await module.link(() => dependency)
    await module.evaluate()
    assert.equal(module.namespace.eventArchiveEnabled, false)
    assert.equal((await module.namespace.changeEventArchive(12, true)).status, "archived")
    assert.equal((await module.namespace.copyEvent(12, "День рождения", "")).id, 13)
    assert.equal(calls[0][1].archived, true)
    assert.equal(calls[1][1].event_date, null)
})
