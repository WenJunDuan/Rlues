#!/usr/bin/env node
// Athena single-source build (athena-10-1 S1). Zero dependencies.
//
//   node vibeCoding/athena/build.mjs [--src <athena>] [--out <dist>] [--platform <name>|all] [--check]
//
// Sources, per platform (adapters/<p>/platform.json):
//   core/package/**            -> <package_root>/**   (platforms with "core": true)
//   adapters/<p>/package/**    -> <package_root>/**
//   adapters/<p>/top/**        -> ./**
//   gate/**                    -> <gate_root>/**     (platforms that set "gate_root"; S2 gate core)
// Generated at the root of every output: contracts.json (from core/pace/stages.yaml),
// GENERATED.md, manifest.json.
//
// Templates: {{athena:NAME}} is replaced by the platform's vars.NAME; {{athena:!NAME}} writes
// the literal {{athena:NAME}}. An undefined or malformed marker, or a marker inside a binary /
// non-UTF-8 file, fails the build. Two sources for one output path (compared case-insensitively,
// as macOS APFS does) fail the build.
//
// Safety: every platform is assembled before anything is written; each output is written to a
// temporary sibling and renamed into place; an existing target is replaced only if it is a
// previous build output (GENERATED.md + manifest.json) inside --out.
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const IGNORED = new Set(["__pycache__", ".DS_Store"]);
const MARKER = "{{athena:";
const TOKEN = /\{\{athena:(!?)([A-Z][A-Z0-9_]*)\}\}/g;
const VERSION_RE = /^\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?$/;
const PLATFORM_RE = /^[a-z][a-z0-9-]*$/;
const GENERATED_TITLE = "# Generated — do not edit\n";
const GENERATED_FILES = ["contracts.json", "GENERATED.md", "manifest.json"];

class BuildError extends Error {}

function parseArgs(argv) {
  const args = { src: path.dirname(fileURLToPath(import.meta.url)), out: null, platform: "all", check: false };
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i];
    if (key === "--check") { args.check = true; continue; }
    if (!["--src", "--out", "--platform"].includes(key)) throw new BuildError(`unknown argument ${key}`);
    if (argv[i + 1] === undefined || argv[i + 1].startsWith("--")) throw new BuildError(`missing value for ${key}`);
    args[key.slice(2)] = argv[++i];
  }
  args.src = path.resolve(args.src);
  args.out = path.resolve(args.out || path.join(args.src, "..", "dist"));
  return args;
}

function walk(root) {
  const files = [];
  if (!fs.existsSync(root)) return files;
  const visit = (dir) => {
    for (const name of fs.readdirSync(dir).sort()) {
      if (IGNORED.has(name)) continue;
      const full = path.join(dir, name);
      const stat = fs.lstatSync(full);
      if (stat.isSymbolicLink()) throw new BuildError(`symlink not allowed: ${full}`);
      if (stat.isDirectory()) visit(full);
      else files.push(full);
    }
  };
  visit(root);
  return files;
}

const posix = (p) => p.split(path.sep).join("/");
const conflictKey = (rel) => rel.normalize("NFC").toLowerCase();

function readJson(file, label) {
  try { return JSON.parse(fs.readFileSync(file, "utf8")); }
  catch (error) { throw new BuildError(`${label}: ${error.message}`); }
}

/** stages.yaml is written in the JSON subset of YAML; whole-line "#" comments are allowed. */
function contracts(src, version) {
  const file = path.join(src, "core/pace/stages.yaml");
  const text = fs.readFileSync(file, "utf8").split("\n").filter(line => !/^\s*#/.test(line)).join("\n");
  let data;
  try { data = JSON.parse(text); } catch (error) { throw new BuildError(`core/pace/stages.yaml: ${error.message}`); }
  const paths = new Set(data.paths || []);
  const seen = new Set();
  const checkPaths = (owner, list) => {
    for (const name of list || []) {
      if (!paths.has(name)) throw new BuildError(`core/pace/stages.yaml: ${owner} names unknown path ${name}`);
    }
  };
  for (const stage of data.stages || []) {
    if (!stage.id || seen.has(stage.id)) throw new BuildError(`core/pace/stages.yaml: missing or duplicate stage id ${stage.id}`);
    seen.add(stage.id);
    for (const key of ["paths", "optional_paths", "skip_paths"]) checkPaths(`stage ${stage.id} ${key}`, stage[key]);
    for (const item of [...(stage.produces || []), ...(stage.gates || [])]) {
      if (item && typeof item === "object") checkPaths(`stage ${stage.id} ${item.file || item.check}`, item.paths);
    }
    for (const rule of stage.hard || []) {
      if (!data.hard || !data.hard[rule]) throw new BuildError(`core/pace/stages.yaml: stage ${stage.id} names unknown hard rule ${rule}`);
    }
    for (const rule of stage.advisory || []) {
      if (!data.advisory || !data.advisory[rule]) throw new BuildError(`core/pace/stages.yaml: stage ${stage.id} names unknown advisory ${rule}`);
    }
  }
  for (const [rule, spec] of Object.entries(data.hard || {})) checkPaths(`hard ${rule}`, spec.paths);
  return `${JSON.stringify({ schema: 1, version, source: "core/pace/stages.yaml", ...data }, null, 2)}\n`;
}

function render(buffer, vars, label) {
  if (!buffer.includes(MARKER)) return buffer;
  let text;
  try {
    if (buffer.includes(0)) throw new Error("NUL byte");
    text = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(buffer);
  } catch (_) {
    throw new BuildError(`${label}: template marker in a binary or non-UTF-8 file`);
  }
  const malformed = text.replace(TOKEN, "");
  if (malformed.includes(MARKER)) {
    const at = malformed.indexOf(MARKER);
    throw new BuildError(`${label}: malformed template marker near "${malformed.slice(at, at + 40).split("\n")[0]}"`);
  }
  const missing = new Set();
  const rendered = text.replace(TOKEN, (match, literal, name) => {
    if (literal) return `${MARKER}${name}}}`;
    if (!Object.prototype.hasOwnProperty.call(vars, name)) { missing.add(name); return match; }
    return vars[name];
  });
  if (missing.size) throw new BuildError(`${label}: undefined variable ${[...missing].join(", ")}`);
  return Buffer.from(rendered, "utf8");
}

function assemble(src, platform, version) {
  const config = readJson(path.join(src, "adapters", platform, "platform.json"), `adapters/${platform}/platform.json`);
  const dir = config.dist_dir || platform;
  if (!PLATFORM_RE.test(dir)) throw new BuildError(`adapters/${platform}/platform.json: invalid dist_dir ${dir}`);
  const vars = config.vars || {};
  const root = config.package_root || "";
  if (root && (path.isAbsolute(root) || root.split(/[\\/]/).includes(".."))) {
    throw new BuildError(`adapters/${platform}/platform.json: invalid package_root ${root}`);
  }
  const layers = [];
  if (config.core) layers.push({ dir: path.join(src, "core/package"), prefix: root, label: "core/package" });
  if (config.gate_root !== undefined) {
    const gateRoot = config.gate_root;
    if (typeof gateRoot !== "string" || path.isAbsolute(gateRoot) || gateRoot.split(/[\\/]/).includes("..")) {
      throw new BuildError(`adapters/${platform}/platform.json: invalid gate_root ${gateRoot}`);
    }
    layers.push({ dir: path.join(src, "gate"), prefix: gateRoot, label: "gate" });
  }
  layers.push({ dir: path.join(src, "adapters", platform, "package"), prefix: root, label: `adapters/${platform}/package` });
  layers.push({ dir: path.join(src, "adapters", platform, "top"), prefix: "", label: `adapters/${platform}/top` });
  const outputs = new Map();
  const keys = new Map();
  const claim = (rel, source) => {
    const key = conflictKey(rel);
    if (keys.has(key)) throw new BuildError(`conflict: ${rel} comes from ${keys.get(key)} and ${source}`);
    keys.set(key, source);
  };
  for (const name of GENERATED_FILES) claim(name, "build.mjs");
  for (const layer of layers) {
    for (const file of walk(layer.dir)) {
      const rel = posix(path.join(layer.prefix, path.relative(layer.dir, file)));
      const source = `${layer.label}/${posix(path.relative(layer.dir, file))}`;
      claim(rel, source);
      const mode = fs.statSync(file).mode & 0o111 ? 0o755 : 0o644;
      outputs.set(rel, { content: render(fs.readFileSync(file), vars, source), mode, source });
    }
  }
  const generated = (content, source = "build.mjs") => ({ content: Buffer.from(content, "utf8"), mode: 0o644, source });
  outputs.set("contracts.json", generated(contracts(src, version), "core/pace/stages.yaml"));
  outputs.set("GENERATED.md", generated(
    `${GENERATED_TITLE}\nEvery file in this tree is generated by \`vibeCoding/athena/build.mjs\` (Athena ${version}, platform ${platform}).\n` +
    "Edit the sources under `vibeCoding/athena/` and rebuild. `manifest.json` lists each file's sha256, mode and source.\n"));
  const files = [...outputs.keys()].sort().map(rel => ({
    path: rel,
    sha256: crypto.createHash("sha256").update(outputs.get(rel).content).digest("hex"),
    mode: outputs.get(rel).mode.toString(8).padStart(4, "0"),
    source: outputs.get(rel).source,
  }));
  outputs.set("manifest.json", generated(`${JSON.stringify({ schema: 1, platform, version, files }, null, 2)}\n`));
  return { dir, outputs };
}

/** Only a previous build output inside --out may be replaced. */
function assertReplaceable(out, target) {
  const rel = path.relative(out, target);
  if (!rel || rel.startsWith("..") || path.isAbsolute(rel)) throw new BuildError(`refusing to write ${target}: not inside ${out}`);
  if (!fs.existsSync(target)) return;
  if (!fs.statSync(target).isDirectory()) throw new BuildError(`refusing to replace ${target}: not a directory`);
  if (fs.readdirSync(target).length === 0) return;
  const marker = path.join(target, "GENERATED.md");
  const ok = fs.existsSync(marker) && fs.existsSync(path.join(target, "manifest.json"))
    && fs.readFileSync(marker, "utf8").startsWith(GENERATED_TITLE);
  if (!ok) throw new BuildError(`refusing to replace ${target}: not a previous build output (no GENERATED.md + manifest.json)`);
}

function writeTree(out, target, outputs) {
  assertReplaceable(out, target);
  const staging = `${target}.tmp-${process.pid}`;
  fs.rmSync(staging, { recursive: true, force: true });
  for (const rel of [...outputs.keys()].sort()) {
    const file = path.join(staging, ...rel.split("/"));
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, outputs.get(rel).content);
    fs.chmodSync(file, outputs.get(rel).mode);
  }
  fs.rmSync(target, { recursive: true, force: true });
  fs.renameSync(staging, target);
}

function compareTree(target, outputs) {
  const problems = [];
  const present = new Set(walk(target).map(file => posix(path.relative(target, file))));
  for (const rel of [...outputs.keys()].sort()) {
    const file = path.join(target, ...rel.split("/"));
    const expected = outputs.get(rel);
    if (!present.has(rel)) { problems.push(`missing ${rel}`); continue; }
    present.delete(rel);
    if (!fs.readFileSync(file).equals(expected.content)) problems.push(`differs ${rel}`);
    if (Boolean(fs.statSync(file).mode & 0o111) !== Boolean(expected.mode & 0o111)) problems.push(`mode ${rel}`);
  }
  for (const rel of [...present].sort()) problems.push(`unexpected ${rel}`);
  return problems;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const version = fs.readFileSync(path.join(args.src, "VERSION"), "utf8").trim();
  if (!VERSION_RE.test(version)) throw new BuildError(`VERSION must look like 10.1.0 or 10.1.0-dev, got "${version}"`);
  const release = version.split("-")[0].split(".").slice(0, 2).join(".");
  const available = fs.readdirSync(path.join(args.src, "adapters"))
    .filter(name => PLATFORM_RE.test(name) && fs.existsSync(path.join(args.src, "adapters", name, "platform.json"))).sort();
  if (args.platform !== "all" && !available.includes(args.platform)) {
    throw new BuildError(`unknown platform ${args.platform}; available: ${available.join(", ")}`);
  }
  const platforms = args.platform === "all" ? available : [args.platform];
  const built = platforms.map(platform => ({ platform, ...assemble(args.src, platform, version) }));
  const dirs = new Map();
  for (const { platform, dir } of built) {
    if (dirs.has(dir)) throw new BuildError(`adapters ${dirs.get(dir)} and ${platform} share dist_dir ${dir}`);
    dirs.set(dir, platform);
  }
  if (!args.check) {
    for (const { dir } of built) assertReplaceable(args.out, path.join(args.out, dir, release));
  }
  let failed = false;
  for (const { dir, outputs } of built) {
    const target = path.join(args.out, dir, release);
    if (args.check) {
      const problems = compareTree(target, outputs);
      for (const problem of problems) process.stderr.write(`[athena-build] ${dir}/${release}: ${problem}\n`);
      failed = failed || problems.length > 0;
    } else {
      writeTree(args.out, target, outputs);
      process.stdout.write(`[athena-build] ${dir}/${release}: ${outputs.size} files\n`);
    }
  }
  if (failed) process.exitCode = 1;
}

try {
  main();
} catch (error) {
  process.stderr.write(`[athena-build] ${error instanceof BuildError ? error.message : error.stack}\n`);
  process.exitCode = 2;
}
