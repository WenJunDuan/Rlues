#!/usr/bin/env node
/**
 * VibeCoding Athena v9.6.4 · CC PostToolUse(Edit|Write|MultiEdit) hook
 *
 * 职责: 扫描 .ai_state/ 子目录, 更新 _index.md frontmatter 的 counts + pointers.
 *
 * v9.6.4 改动 (vs v9.6.2):
 *   - sprints/{date}-{slug}/ 替代 details/ → 扫 sprint 目录分类计数
 *   - compound/{date}-{doc_type}-{slug}.md 替代 lessons.md → 按 doc_type 计数
 *   - 维护 pointers.latest_decisions (近 5 个 decision-*.md, mtime desc)
 *   - 维护 pointers.latest_lessons (近 5 个 learning-*.md)
 *   - 维护 pointers.latest_architecture_update (architecture/ARCHITECTURE.md mtime)
 *
 * 非阻塞: 任何异常 exit 0 + stderr 提示
 */
'use strict';

const fs = require('fs');
const path = require('path');

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

function listDirs(p) {
  if (!fs.existsSync(p)) return [];
  return fs.readdirSync(p, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => d.name);
}

function listFiles(p) {
  if (!fs.existsSync(p)) return [];
  return fs.readdirSync(p, { withFileTypes: true })
    .filter(d => d.isFile())
    .map(d => d.name);
}

function readSprintPath(sprintDir) {
  // 读 sprint 目录中第一个含 path 字段的文件 (design.md 或 brainstorm.md)
  for (const candidate of ['design.md', 'brainstorm.md', 'checklist.yaml']) {
    const fp = path.join(sprintDir, candidate);
    if (fs.existsSync(fp)) {
      const content = fs.readFileSync(fp, 'utf-8');
      const m = content.match(/^path:\s*["']?(\w+)["']?/m);
      if (m) return m[1];
    }
  }
  return '';
}

function parseDocType(filename) {
  // compound/{YYYY-MM-DD}-{doc_type}-{slug}.md
  const m = filename.match(/^\d{4}-\d{2}-\d{2}-(\w+)-.*\.md$/);
  return m ? m[1] : null;
}

function scanSprints(aiState) {
  const sprintsDir = path.join(aiState, 'sprints');
  const dirs = listDirs(sprintsDir);
  const counts = { features: 0, issues: 0, refactors: 0, systems: 0, reviews: 0, cleanup: 0 };
  for (const d of dirs) {
    const sprintDir = path.join(sprintsDir, d);
    const pathType = readSprintPath(sprintDir);
    if (pathType === 'Feature' || pathType === 'Quick' || pathType === 'Hotfix') counts.features++;
    else if (pathType === 'Bugfix') counts.issues++;
    else if (pathType === 'Refactor') counts.refactors++;
    else if (pathType === 'System') counts.systems++;
    // reviews + cleanup 计数: 每个 sprint 内的 reviews/pass*.md 和 cleanup-pass.md
    const reviewsDir = path.join(sprintDir, 'reviews');
    counts.reviews += listFiles(reviewsDir).filter(f => f.endsWith('.md')).length;
    if (fs.existsSync(path.join(sprintDir, 'cleanup-pass.md'))) counts.cleanup++;
  }
  return counts;
}

function scanCompound(aiState) {
  const compoundDir = path.join(aiState, 'compound');
  const files = listFiles(compoundDir);
  const counts = { learning: 0, trick: 0, decision: 0, explore: 0 };
  const byType = { learning: [], trick: [], decision: [], explore: [] };
  for (const f of files) {
    const docType = parseDocType(f);
    if (docType && counts.hasOwnProperty(docType)) {
      counts[docType]++;
      const fp = path.join(compoundDir, f);
      byType[docType].push({ name: f, mtime: fs.statSync(fp).mtimeMs });
    }
  }
  // 排序 mtime desc, 取 latest 5
  for (const t of Object.keys(byType)) {
    byType[t].sort((a, b) => b.mtime - a.mtime);
    byType[t] = byType[t].slice(0, 5).map(item => `compound/${item.name}`);
  }
  return { counts, byType };
}

function scanArchitecture(aiState) {
  const archFile = path.join(aiState, 'architecture', 'ARCHITECTURE.md');
  if (!fs.existsSync(archFile)) return '';
  return new Date(fs.statSync(archFile).mtimeMs).toISOString();
}

function scanRequirements(aiState) {
  // v9.8.0: requirements/{slug}.md 长效需求档计数 + 最新指针
  const reqDir = path.join(aiState, 'requirements');
  const files = listFiles(reqDir).filter(f => f.endsWith('.md'));
  let latest = '';
  let latestMtime = 0;
  for (const f of files) {
    const m = fs.statSync(path.join(reqDir, f)).mtimeMs;
    if (m > latestMtime) { latestMtime = m; latest = `requirements/${f}`; }
  }
  return { count: files.length, latest };
}

function updateField(content, field, value) {
  const valueStr = Array.isArray(value)
    ? `[${value.map(v => `"${v}"`).join(', ')}]`
    : (typeof value === 'number' ? value : `"${value}"`);
  const re = new RegExp(`^(\\s*${field}:\\s*).*$`, 'm');
  if (re.test(content)) {
    return content.replace(re, `$1${valueStr}`);
  }
  return content;
}

function updateNestedField(content, parentField, childField, value) {
  // 找 parent: ... 段内的 child 行, 缩进 2 格
  const re = new RegExp(`^(\\s+${childField}:\\s*).*$`, 'm');
  if (re.test(content)) {
    return content.replace(re, `$1${typeof value === 'number' ? value : `"${value}"`}`);
  }
  return content;
}

function main() {
  try {
    const aiState = findAiState(process.cwd());
    if (!aiState) { process.exit(0); }

    const idxPath = path.join(aiState, '_index.md');
    if (!fs.existsSync(idxPath)) { process.exit(0); }

    let content = fs.readFileSync(idxPath, 'utf-8');

    // 1. 扫 sprints/
    const sprintCounts = scanSprints(aiState);
    content = updateField(content, 'features_count', sprintCounts.features);
    content = updateField(content, 'issues_count', sprintCounts.issues);
    content = updateField(content, 'refactors_count', sprintCounts.refactors);
    content = updateField(content, 'systems_count', sprintCounts.systems);
    content = updateField(content, 'reviews_count', sprintCounts.reviews);
    content = updateField(content, 'cleanup_count', sprintCounts.cleanup);

    // 2. 扫 compound/
    const { counts: cmpCounts, byType } = scanCompound(aiState);
    // compound nested counts (在 counts.compound 下)
    content = updateNestedField(content, 'compound', 'learning', cmpCounts.learning);
    content = updateNestedField(content, 'compound', 'trick', cmpCounts.trick);
    content = updateNestedField(content, 'compound', 'decision', cmpCounts.decision);
    content = updateNestedField(content, 'compound', 'explore', cmpCounts.explore);

    // 3. pointers.latest_decisions + latest_lessons
    content = updateField(content, 'latest_decisions', byType.decision);
    content = updateField(content, 'latest_lessons', byType.learning);

    // 4. pointers.latest_architecture_update
    const archMtime = scanArchitecture(aiState);
    if (archMtime) {
      content = updateField(content, 'latest_architecture_update', archMtime);
    }

    // 5. v9.8.0: requirements/ count + latest pointer
    const req = scanRequirements(aiState);
    content = updateField(content, 'requirements_count', req.count);
    if (req.latest) content = updateField(content, 'latest_requirement', req.latest);

    fs.writeFileSync(idxPath, content, 'utf-8');
    process.exit(0);
  } catch (e) {
    process.stderr.write(`[index-updater] non-blocking: ${e.message}\n`);
    process.exit(0);
  }
}

main();
