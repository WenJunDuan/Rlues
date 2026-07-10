#!/usr/bin/env node
/**
 * VibeCoding Athena v9.9.1 · CC Stop hook (token-usage-collector)
 *
 * 职责:
 *   1. 从 Stop/SubagentStop payload.transcript_path/agent_transcript_path 或 payload 内递归提取 usage/token_count
 *   2. 按 sprint 写入 sprints/{slug}/token-usage.yaml
 *   3. 无 usage 字段时写明 no_usage_found, 不猜 token
 *
 * 平台边界:
 *   - Claude Code hooks: https://code.claude.com/docs/en/hooks
 *   - Stop hook payload 提供 transcript_path 时可从 JSONL transcript 聚合 usage.
 *
 * 非阻塞: 任何异常 exit 0.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const TOKEN_FIELDS = [
  'cache_creation_input_tokens',
  'cache_read_input_tokens',
  'cached_input_tokens',
  'input_tokens',
  'output_tokens',
  'reasoning_output_tokens',
  'total_tokens',
];

function findAiState(cwd) {
  let current = cwd;
  for (let i = 0; i < 5; i++) {
    const candidate = path.join(current, '.ai_state');
    if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) return candidate;
    const parent = path.dirname(current);
    if (parent === current) return null;
    current = parent;
  }
  return null;
}

function readField(idxPath, field) {
  try {
    const content = fs.readFileSync(idxPath, 'utf-8');
    const match = content.match(new RegExp(`^${field}:\\s*["']?([^"\\n]*)["']?`, 'm'));
    return match ? match[1].trim() : '';
  } catch (_) {
    return '';
  }
}

function readPayload() {
  try {
    const data = fs.readFileSync(0, 'utf-8');
    return data ? JSON.parse(data) : {};
  } catch (_) {
    return {};
  }
}

function asInt(value) {
  const n = Number.parseInt(value || 0, 10);
  return Number.isFinite(n) ? n : 0;
}

function hasUsageShape(raw) {
  return raw && typeof raw === 'object' && TOKEN_FIELDS.some(k => Object.prototype.hasOwnProperty.call(raw, k));
}

function normalizeUsage(raw) {
  const usage = {};
  for (const field of TOKEN_FIELDS) usage[field] = asInt(raw[field]);
  if (!usage.cached_input_tokens) {
    usage.cached_input_tokens = usage.cache_creation_input_tokens + usage.cache_read_input_tokens;
  }
  if (!usage.total_tokens) {
    usage.total_tokens = usage.input_tokens + usage.output_tokens;
  }
  return usage;
}

function fingerprint(record) {
  const stable = {};
  for (const [key, value] of Object.entries(record)) {
    if (key !== 'stage' && key !== 'fingerprint') stable[key] = value;
  }
  if (Object.prototype.hasOwnProperty.call(stable, '_fingerprint_timestamp')) {
    stable.timestamp = stable._fingerprint_timestamp;
    delete stable._fingerprint_timestamp;
  }
  const body = JSON.stringify(stable, Object.keys(stable).sort());
  return crypto.createHash('sha256').update(body).digest('hex').slice(0, 16);
}

function makeRecord({ platform, stage, sourceType, sourceId, timestamp, model, usage }) {
  const displayTimestamp = timestamp || new Date().toISOString();
  const record = {
    platform,
    stage: stage || 'unknown',
    source_type: sourceType,
    source_id: sourceId,
    timestamp: displayTimestamp,
    _fingerprint_timestamp: timestamp || '',
    model: model || 'unknown',
    ...usage,
  };
  record.fingerprint = fingerprint(record);
  delete record._fingerprint_timestamp;
  return record;
}

function usageFromTextBlock(text) {
  const blocks = [];
  for (const match of text.matchAll(/<usage>(.*?)<\/usage>/gis)) {
    const raw = match[1].trim();
    let parsed = null;
    try {
      const value = JSON.parse(raw);
      parsed = value && typeof value === 'object' && value.usage && typeof value.usage === 'object'
        ? value.usage
        : value;
    } catch (_) {
      parsed = null;
    }
    if (hasUsageShape(parsed)) {
      blocks.push(normalizeUsage(parsed));
      continue;
    }

    const fields = {};
    for (const field of [...TOKEN_FIELDS, 'subagent_tokens']) {
      const fieldMatch = raw.match(new RegExp(`\\b${field}\\b\\s*[:=]\\s*(\\d+)`));
      if (fieldMatch) fields[field] = asInt(fieldMatch[1]);
    }
    if (/^\d+$/.test(raw)) fields.total_tokens = asInt(raw);
    if (fields.subagent_tokens && !fields.total_tokens) fields.total_tokens = fields.subagent_tokens;
    if (Object.keys(fields).length) blocks.push(normalizeUsage(fields));
  }
  return blocks;
}

function collectFromObj(obj, ctx) {
  const records = [];
  if (Array.isArray(obj)) {
    for (const item of obj) records.push(...collectFromObj(item, ctx));
    return records;
  }
  if (typeof obj === 'string') {
    for (const usage of usageFromTextBlock(obj)) {
      records.push(makeRecord({
        platform: ctx.platform,
        stage: ctx.stage,
        sourceType: ctx.sourceType,
        sourceId: ctx.sourceId,
        timestamp: ctx.timestamp || '',
        model: ctx.model || '',
        usage,
      }));
    }
    return records;
  }
  if (!obj || typeof obj !== 'object') return records;

  const current = {
    ...ctx,
    timestamp: obj.timestamp || obj.ts || ctx.timestamp || '',
    model: obj.model || ctx.model || '',
  };

  const payload = obj.payload;
  if (payload && typeof payload === 'object' && payload.type === 'token_count') {
    const info = payload.info && typeof payload.info === 'object' ? payload.info : {};
    if (hasUsageShape(info.last_token_usage)) {
      records.push(makeRecord({
        platform: current.platform,
        stage: current.stage,
        sourceType: current.sourceType,
        sourceId: current.sourceId,
        timestamp: current.timestamp,
        model: current.model,
        usage: normalizeUsage(info.last_token_usage),
      }));
    }
  }

  if (hasUsageShape(obj.usage)) {
    records.push(makeRecord({
      platform: current.platform,
      stage: current.stage,
      sourceType: current.sourceType,
      sourceId: current.sourceId,
      timestamp: current.timestamp,
      model: current.model,
      usage: normalizeUsage(obj.usage),
    }));
  }

  for (const value of Object.values(obj)) {
    if (value && (typeof value === 'object' || typeof value === 'string')) {
      records.push(...collectFromObj(value, current));
    }
  }
  return records;
}

function collectFromTranscript(transcriptPath, platform, stage, sourceType = 'transcript_path') {
  if (!transcriptPath) return [];
  const fp = path.resolve(transcriptPath.replace(/^~/, process.env.HOME || ''));
  if (!fs.existsSync(fp) || !fs.statSync(fp).isFile()) return [];
  const records = [];
  for (const line of fs.readFileSync(fp, 'utf-8').split('\n')) {
    if (!line.trim()) continue;
    try {
      const item = JSON.parse(line);
      records.push(...collectFromObj(item, {
        platform,
        stage,
        sourceType,
        sourceId: fp,
      }));
    } catch (_) {
      // Ignore malformed transcript rows.
    }
  }
  return records;
}

function readExistingRecords(file) {
  if (!fs.existsSync(file)) return [];
  const content = fs.readFileSync(file, 'utf-8');
  const records = [];
  let current = null;
  for (const line of content.split('\n')) {
    const start = line.match(/^\s*- fingerprint:\s*"([^"]+)"/);
    if (start) {
      if (current) records.push(current);
      current = { fingerprint: start[1] };
      continue;
    }
    if (!current) continue;
    const field = line.match(/^\s{4}([\w_]+):\s*(.*)$/);
    if (!field) continue;
    const key = field[1];
    const raw = field[2].trim();
    if (TOKEN_FIELDS.includes(key)) {
      current[key] = asInt(raw);
    } else {
      try {
        current[key] = JSON.parse(raw);
      } catch (_) {
        current[key] = raw.replace(/^"|"$/g, '');
      }
    }
  }
  if (current) records.push(current);
  return records;
}

function quote(value) {
  return JSON.stringify(String(value));
}

function yamlScalar(value) {
  return value == null ? 'null' : String(value);
}

function sleep(ms) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

function acquireLock(file) {
  const lock = `${file}.lock`;
  const deadline = Date.now() + 5000;
  while (true) {
    try {
      const fd = fs.openSync(lock, 'wx', 0o600);
      return { fd, lock };
    } catch (err) {
      if (err && err.code !== 'EEXIST') throw err;
      if (Date.now() >= deadline) throw new Error(`timeout acquiring ${lock}`);
      sleep(50);
    }
  }
}

function atomicWrite(file, content) {
  const tmp = `${file}.tmp`;
  fs.writeFileSync(tmp, content, 'utf-8');
  fs.renameSync(tmp, file);
}

function writeUsageYaml(file, sprintSlug, records, note) {
  const totals = {};
  for (const field of TOKEN_FIELDS) totals[field] = 0;
  const byModel = {};
  const byStage = {};

  for (const record of records) {
    const stage = record.stage || 'unknown';
    const model = record.model || 'unknown';
    if (!byModel[model]) {
      byModel[model] = { calls: 0 };
      for (const field of TOKEN_FIELDS) byModel[model][field] = 0;
    }
    if (!byStage[stage]) byStage[stage] = {};
    if (!byStage[stage][model]) {
      byStage[stage][model] = { calls: 0 };
      for (const field of TOKEN_FIELDS) byStage[stage][model][field] = 0;
    }
    byModel[model].calls += 1;
    byStage[stage][model].calls += 1;
    for (const field of TOKEN_FIELDS) {
      const value = asInt(record[field]);
      totals[field] += value;
      byModel[model][field] += value;
      byStage[stage][model][field] += value;
    }
  }

  const lines = [
    `sprint_slug: ${sprintSlug}`,
    `updated_at: ${quote(new Date().toISOString())}`,
    `status: ${quote(records.length ? 'ok' : 'no_usage_found')}`,
    'totals:',
  ];
  for (const field of [...TOKEN_FIELDS].sort()) {
    lines.push(`  ${field}: ${yamlScalar(records.length ? totals[field] : null)}`);
  }
  lines.push('by_model:');
  const models = Object.keys(byModel).sort();
  if (models.length) {
    for (const model of models) {
      lines.push(`  ${quote(model)}:`);
      for (const [key, value] of Object.entries(byModel[model])) lines.push(`    ${key}: ${value}`);
    }
  } else {
    lines.push('  {}');
  }
  lines.push('by_stage:');
  const stages = Object.keys(byStage).sort();
  if (stages.length) {
    for (const stage of stages) {
      lines.push(`  ${quote(stage)}:`);
      for (const model of Object.keys(byStage[stage]).sort()) {
        lines.push(`    ${quote(model)}:`);
        for (const [key, value] of Object.entries(byStage[stage][model])) {
          lines.push(`      ${key}: ${value}`);
        }
      }
    }
  } else {
    lines.push('  {}');
  }
  lines.push('records:');
  if (records.length) {
    for (const record of records) {
      lines.push(`  - fingerprint: ${quote(record.fingerprint)}`);
      for (const key of [
        'platform',
        'stage',
        'source_type',
        'source_id',
        'timestamp',
        'model',
        ...[...TOKEN_FIELDS].sort(),
      ]) {
        const value = record[key] || 0;
        if (Number.isInteger(value)) lines.push(`    ${key}: ${value}`);
        else lines.push(`    ${key}: ${quote(value)}`);
      }
    }
  } else {
    lines.push('  []');
  }
  lines.push('notes:');
  if (note) lines.push(`  - ${quote(note)}`);
  else lines.push('  []');
  atomicWrite(file, `${lines.join('\n')}\n`);
}

function main() {
  try {
    const payload = readPayload();
    const cwd = payload.cwd || process.cwd();
    const aiState = findAiState(cwd);
    if (!aiState) process.exit(0);

    const idx = path.join(aiState, '_index.md');
    const sprintSlug = readField(idx, 'current_sprint_slug');
    const stage = readField(idx, 'stage');
    if (!sprintSlug) process.exit(0);

    const sprintDir = path.join(aiState, 'sprints', sprintSlug);
    fs.mkdirSync(sprintDir, { recursive: true });
    const out = path.join(sprintDir, 'token-usage.yaml');

    const records = [];
    const seenTranscriptPaths = new Set();
    for (const [field, sourceType] of [
      ['transcript_path', 'transcript_path'],
      ['session_path', 'transcript_path'],
      ['agent_transcript_path', 'agent_transcript_path'],
    ]) {
      const transcriptPath = payload[field] || '';
      if (!transcriptPath) continue;
      const resolved = path.resolve(String(transcriptPath).replace(/^~/, process.env.HOME || ''));
      if (seenTranscriptPaths.has(resolved)) continue;
      seenTranscriptPaths.add(resolved);
      records.push(...collectFromTranscript(transcriptPath, 'cc', stage, sourceType));
    }
    records.push(...collectFromObj(payload, {
      platform: 'cc',
      stage,
      sourceType: 'hook_payload',
      sourceId: payload.hook_event_name || payload.event || 'Stop',
    }));

    const { fd, lock } = acquireLock(out);
    try {
      const existing = readExistingRecords(out);
      const seen = new Set(existing.map(record => record.fingerprint).filter(Boolean));
      const deduped = [...existing];
      for (const record of records) {
        if (record.fingerprint && !seen.has(record.fingerprint)) {
          seen.add(record.fingerprint);
          deduped.push(record);
        }
      }

      const note = deduped.length
        ? ''
        : 'No usage fields found in Claude hook payload/transcript_path; keep token totals unknown.';
      writeUsageYaml(out, sprintSlug, deduped, note);
    } finally {
      fs.closeSync(fd);
      try { fs.unlinkSync(lock); } catch (_) {}
    }
    process.exit(0);
  } catch (err) {
    process.stderr.write(`[token-usage-collector] non-blocking: ${err.message}\n`);
    process.exit(0);
  }
}

main();
