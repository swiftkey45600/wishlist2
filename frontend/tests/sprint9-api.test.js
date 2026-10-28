import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import test from "node:test"
import vm from "node:vm"

async function repository(name, api) {
    const context = vm.createContext({})
    const dependency = new vm.SyntheticModule(["default"], function () { this.setExport("default", api) }, { context })
    const source = await readFile(new URL(`../src/repositories/${name}.js`, import.meta.url), "utf8")
    const module = new vm.SourceTextModule(source, { context, initializeImportMeta(meta) { meta.env = {} } })
    await module.link(() => dependency)
    await module.evaluate()
    return module.namespace
}

test("questions use public token for guest requests and owner route for answers", async () => {
    const calls = []
    const api = {
        get: async path => { calls.push(["get", path]); return { data: [] } },
        post: async (path, data) => { calls.push(["post", path, data]); return { data: { id: 2 } } },
        patch: async (path, data) => { calls.push(["patch", path, data]); return { data: { id: 2 } } }
    }
    const questions = await repository("giftQuestionRepository", api)
    await questions.fetchQuestions("public token", 7)
    await questions.createQuestion("public token", 7, "Гость", "Какой цвет?")
    await questions.answerQuestion(7, 2, "Синий")
    assert.equal(calls[0][1], "/events/public/public%20token/gifts/7/questions")
    assert.equal(calls[1][2].guest_name, "Гость")
    assert.equal(calls[1][2].text, "Какой цвет?")
    assert.equal(calls[2][1], "/gifts/7/questions/2/answer")
    assert.equal(calls[2][2].answer, "Синий")
    assert.equal(questions.questionDeletionEnabled, true)
})

test("email features use the implemented API", async () => {
    const calls = []
    const email = await repository("accountEmailRepository", { post: async (path, body) => { calls.push([path, body]) } })
    assert.equal(email.emailFeaturesEnabled, true)
    await email.resetPassword("token", "password")
    await email.requestEmailVerification()
    assert.equal(calls[0][0], "/auth/password-reset/confirm")
    assert.equal(calls[0][1].new_password, "password")
    assert.equal(calls[1][0], "/auth/email/verification/request")
})
