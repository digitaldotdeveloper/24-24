// Queues image jobs on the local Gemini Studio dashboard, saves results to ../_src/<name>.png
//   node gen.mjs [wave-size] [name,name,...]
// Re-running skips anything already in _src/, so it doubles as the retry pass.
import { readFile, writeFile, access } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const HOST = 'http://127.0.0.1:4321'
const TOKEN = process.env.GS_TOKEN   // Gemini Studio -> Settings -> API tokens
if (!TOKEN) { console.error('set GS_TOKEN first'); process.exit(1) }
const H = { 'content-type': 'application/json', authorization: 'Bearer ' + TOKEN }
const here = path.dirname(fileURLToPath(import.meta.url))
const out = path.join(here, '..', '_src')

const post = async (route, body) => {
  const r = await fetch(HOST + route, { method: 'POST', headers: H, body: JSON.stringify(body) })
  if (!r.ok) throw new Error(`${route} -> ${r.status}`)
  return r.json()
}
const state = async () => (await fetch(HOST + '/api/state', { headers: H })).json()
const exists = (f) => access(f).then(() => true, () => false)
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const stamp = () => new Date().toTimeString().slice(0, 8)

const WAVE = parseInt(process.argv[2] || '8', 10)
const only = process.argv[3]
let jobs = JSON.parse(await readFile(path.join(here, 'jobs.json'), 'utf8'))
if (only) jobs = jobs.filter((j) => only.split(',').includes(j.name))

const todo = []
for (const j of jobs) {
  const dest = path.join(out, j.name + '.png')
  if (await exists(dest)) { console.log('skip', j.name); continue }
  todo.push({ ...j, dest })
}
console.log(`${stamp()} ${todo.length} to render, waves of ${WAVE}`)

const failed = []
for (let w = 0; w < todo.length; w += WAVE) {
  const wave = todo.slice(w, w + WAVE)
  for (const q of wave) {
    // Gemini throttles hard; one queue call per job, the server paces them at concurrency 4
    const { queued } = await post('/api/generate', {
      prompt: q.prompt, mode: 'image', model: 'Pro', runs: 1, threadId: null, attach: [],
    })
    q.id = queued[0]
    console.log(`${stamp()} queued ${q.name} ${q.id}`)
  }
  const pending = new Set(wave.map((q) => q.id))
  const deadline = Date.now() + 25 * 60e3
  while (pending.size && Date.now() < deadline) {
    await sleep(5000)
    const s = await state()
    for (const q of wave) {
      if (!pending.has(q.id)) continue
      const job = s.jobs.find((x) => x.id === q.id)
      if (!job || !['done', 'failed', 'cancelled'].includes(job.status)) continue
      pending.delete(q.id)
      // match on jobId, never on library order — the library is global across sessions
      const entry = s.library.find((i) => i.jobId === q.id && (i.kind || 'image') === 'image')
      if (job.status !== 'done' || !entry) {
        failed.push(q.name)
        console.log(`${stamp()} FAILED ${q.name} ${job.status} ${job.error || ''}`)
        continue
      }
      const r = await fetch(`${HOST}/images/${entry.file}`, { headers: H })
      await writeFile(q.dest, Buffer.from(await r.arrayBuffer()))
      console.log(`${stamp()} saved  ${q.name}`)
    }
  }
  for (const id of pending) {
    const q = wave.find((x) => x.id === id)
    failed.push(q.name)
    console.log(`${stamp()} TIMEOUT ${q.name}`)
  }
}
console.log(`${stamp()} done. failed: ${failed.join(',') || 'none'}`)
