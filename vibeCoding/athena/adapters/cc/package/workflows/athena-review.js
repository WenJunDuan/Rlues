// Athena review workflow (flag cc_workflows; installed by `athena install` only when the flag is on).
// prepare → one reviewer per dimension in parallel → adversarial check of each finding → accept.
// Unverified (S7 probe): the reviewer agents run with the default agent type; read-only is by prompt.
// The CLI stays the only writer of review.json; this script only orchestrates.
export const meta = {
  name: 'athena-review',
  description: 'Athena: prepare a review packet, review it per dimension in parallel, verify findings, accept into review.json',
  phases: [{ title: 'Prepare' }, { title: 'Review' }, { title: 'Verify' }, { title: 'Accept' }],
}

const ATHENA = 'node ~/.athena/current/cli.cjs'
const DIMENSIONS = ['spec coverage per AC (MISSING/EXTRA/DEVIATED)', 'correctness', 'security', 'test risk', 'over-engineering']
const FINDINGS = {
  type: 'object',
  properties: { findings: { type: 'array', items: { type: 'object', properties: {
    sev: { enum: ['P0', 'P1', 'P2', 'P3'] }, loc: { type: 'string' }, text: { type: 'string' } }, required: ['sev', 'loc', 'text'] } } },
  required: ['findings'],
}
const VERDICT = { type: 'object', properties: { real: { type: 'boolean' }, why: { type: 'string' } }, required: ['real', 'why'] }

const prep = await agent(`Run \`${ATHENA} review prepare\` in the project root. Reply with the run id and the packet path it prints.`,
  { label: 'prepare', phase: 'Prepare', schema: { type: 'object', properties: { run: { type: 'string' }, packet: { type: 'string' } }, required: ['run', 'packet'] } })

if (!prep || !prep.run) return { verdict: 'INCOMPLETE', missing: ['prepare'], accepted: false }

const reviews = await parallel(DIMENSIONS.map(dim => () => agent(
  `You are an independent reviewer for ONE dimension: ${dim}. Read the packet ${prep.packet}, then the code it points to. ` +
  'Read-only: do not edit files. Report only findings in this dimension with a concrete failing input; none is a valid answer.',
  { label: `review:${dim.split(' ')[0]}`, phase: 'Review', schema: FINDINGS })))

// A skipped or dead reviewer must never turn into a PASS (review S3 P1): stop without accepting.
const missing = reviews.map((r, i) => (r ? null : DIMENSIONS[i])).filter(Boolean)
if (missing.length) return { verdict: 'INCOMPLETE', missing, accepted: false }

const all = reviews.flatMap(r => r.findings || [])
const checked = await parallel(all.map(f => () => agent(
  `Adversarially verify this review finding against the code (read-only; try to reproduce it): [${f.sev}] ${f.loc} — ${f.text}. ` +
  'Answer real=false if it does not reproduce or is out of scope.',
  { label: `verify:${f.loc}`, phase: 'Verify', schema: VERDICT }).then(v => ({ ...f, verdict: v }))))

// only an explicit "not real" drops a finding; a missing verifier keeps it
const kept = checked.map((f, i) => f || all[i]).filter(f => !(f.verdict && f.verdict.real === false))
const verdict = kept.some(f => f.sev === 'P0' || f.sev === 'P1') ? 'REWORK' : (kept.length ? 'CONCERNS' : 'PASS')
const output = [...kept.map(f => `- [${f.sev}] ${f.loc} — ${f.text}`), `VERDICT: ${verdict}`].join('\n')

const result = await agent(`Write exactly the text between the markers to a new temporary file outside the repository, then run ` +
  `\`${ATHENA} review accept --run ${prep.run} --file <that file> --family anthropic --platform cc --reviewer-agent athena-review-workflow\`. ` +
  `Report its exit code and its output verbatim.\n<<<\n${output}\n>>>`,
  { label: 'accept', phase: 'Accept', schema: { type: 'object', properties: { exit: { type: 'integer' }, output: { type: 'string' } }, required: ['exit', 'output'] } })

// exit 0 = PASS stored, 3 = non-PASS stored, 4 = source/AC changed since prepare, 2 = refused
return { verdict, run: prep.run, accepted: Boolean(result) && [0, 3].includes(result.exit), accept: result, findings: kept.length, dropped: all.length - kept.length }
