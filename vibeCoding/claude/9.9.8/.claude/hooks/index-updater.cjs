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
 * v9.9.0 新: re-route 机械触发 — sprint 改动文件数超路径上限 (Quick>3 / Feature>10)
 *   且 stage ∈ {impl, runtime-verify} 且 next_action 为空 → 写 next_action="re-route" (只升不降的地板检测)
 *
 * 非阻塞: 任何异常 exit 0 + stderr 提示
 */
'use strict';

const fs = require('fs');
const path = require('path');
const idxio = require('./_index-io.cjs');
const bounds = require('./_index-bounds.cjs');

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
  // v9.9.0 修: 旧实现忽略 parentField, 撞任意同名缩进键 (learning 等键名唯一才没炸).
  // 现限定在 parent 块内: parent 行到下一个同级或更浅缩进行为止.
  const lines = content.split('\n');
  const parentRe = new RegExp(`^(\\s*)${parentField}:\\s*$`);
  const valueStr = typeof value === 'number' ? String(value) : `"${value}"`;
  for (let i = 0; i < lines.length; i++) {
    const pm = lines[i].match(parentRe);
    if (!pm) continue;
    const parentIndent = pm[1].length;
    for (let j = i + 1; j < lines.length; j++) {
      const line = lines[j];
      if (line.trim() === '') continue;
      const indent = (line.match(/^(\s*)/) || ['', ''])[1].length;
      if (indent <= parentIndent) break;   // 出块
      const cm = line.match(new RegExp(`^(\\s+${childField}:\\s*).*$`));
      if (cm) {
        lines[j] = `${cm[1]}${valueStr}`;
        return lines.join('\n');
      }
    }
  }
  return content;
}

function main() {
  try {
    // A3 (2026-07-28, 台账 W22): 按写入面分流 — 写 .ai_state 才重扫 counts/pointers
    // (它们只随 .ai_state 变化); 写实现文件才查 re-route (文件数只随实现写增长)。
    // 旧行为对每次 Edit/Write 全扫 sprints/+compound/, 是纯代码改动的固定税。
    // payload 缺失/无路径 → 保持旧全量行为 (fail-open)。
    let payload = {};
    try { const d = fs.readFileSync(0, 'utf-8'); payload = d ? JSON.parse(d) : {}; } catch (_) {}
    const writtenPath = String(payload?.tool_input?.file_path || payload?.tool_input?.path || '').replace(/\\/g, '/');
    const isStateWrite = writtenPath.includes('.ai_state/');
    const doScan = !writtenPath || isStateWrite;
    const doReroute = !writtenPath || !isStateWrite;

    const aiState = findAiState(payload.cwd || process.cwd());
    if (!aiState) { process.exit(0); }

    const idxPath = path.join(aiState, '_index.md');
    if (!fs.existsSync(idxPath)) { process.exit(0); }
    idxio.acquire(idxPath);   // v9.9.6: 同事件并发写 _index 会丢更新

    let content = fs.readFileSync(idxPath, 'utf-8');
    const contentBefore = content;

    if (doScan) {
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

    }

    // 6. v9.9.0: re-route 机械触发 (铁律[分诊] 地板检测, 只升不降)
    // W36: re-route 与 ship 共享 git 现场变更集; 不依赖普通工具 raw trace 或
    // evidence-collector 的历史 file: 字段, 避免第二账本与停产 tool-trace 漂移。
    const PATH_FILE_CAPS = { Quick: 3, Bugfix: 3, Feature: 10 };
    const fmPath = (content.match(/^path:\s*"?([^"\n]*)"?/m) || [])[1] || '';
    const fmStage = (content.match(/^stage:\s*"?([^"\n]*)"?/m) || [])[1] || '';
    const fmSprint = (content.match(/^current_sprint_slug:\s*"?([^"\n]*)"?/m) || [])[1] || '';
    const fmNextAction = (content.match(/^next_action:\s*"?([^"\n]*)"?/m) || [])[1] || '';

    // hotfix2 AC6/W37: next_action 只允许机器枚举; 进度散文会永久关闭 re-route 且挤占注入。
    const NA_ENUM = /^(|re-route|runtime-verify|review|polish|ship|rework_impl|await-review-result|next_roadmap_item:[A-Za-z0-9._-]+|roadmap_complete)$/;
    if (!NA_ENUM.test(fmNextAction)) {
      process.stderr.write(`[index-updater] next_action 非枚举值 ("${fmNextAction.slice(0,60)}...") — 进度散文请写 route_history/design, next_action 仅存机器信号\n`);
    }
    if (doReroute && PATH_FILE_CAPS[fmPath] && ['impl', 'runtime-verify'].includes(fmStage) && fmSprint && !fmNextAction) {
      // F1/W36 (2026-07-29): tool-trace 已随 hotfix2 停止生成 (W35), re-route 文件数改用
      // 与 ship 同源的 git 现场变更集 — 无第二真相, 无逐工具记账依赖。
      const { execFileSync } = require('child_process');
      const seen = new Set();
      for (const args of [['diff','--name-only'],['diff','--name-only','--cached'],['ls-files','--others','--exclude-standard']]) {
        try {
          for (const f of execFileSync('git', args, { cwd: path.dirname(aiState), encoding: 'utf8', timeout: 10000 }).split('\n')) {
            const fp = f.trim();
            if (fp && !fp.replace(/\\/g,'/').includes('.ai_state/')) seen.add(fp);
          }
        } catch (_) { /* 非 git 环境: 计数 0, 不触发 (fail-open) */ }
      }
        if (seen.size > PATH_FILE_CAPS[fmPath]) {
          content = updateField(content, 'next_action', 're-route');
          process.stderr.write(
            `[index-updater] re-route: path=${fmPath} 改动 ${seen.size} 文件 > 上限 ${PATH_FILE_CAPS[fmPath]} — ` +
            `重走路由审议 (只升不降), _index.route_history 记一条\n`
          );
      }
    }

    content = bounds.enforceIndexBounds(content, aiState);

    if (content !== contentBefore) idxio.writeAtomic(idxPath, content);   // A3: 无变化不写, 减 mtime churn
    process.exit(0);
  } catch (e) {
    process.stderr.write(`[index-updater] non-blocking: ${e.message}\n`);
    process.exit(0);
  }
}

if (require.main === module) main();
else module.exports = { main };
