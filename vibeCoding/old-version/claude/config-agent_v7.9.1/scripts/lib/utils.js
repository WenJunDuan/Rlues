/**
 * VibeCoding Kernel v7.9 - Cross-Platform Utilities
 * Works on Windows, macOS, and Linux
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

// Paths
const HOME = os.homedir();
const CLAUDE_DIR = path.join(HOME, '.claude');
const AI_STATE_DIR = '.ai_state';

/**
 * Ensure directory exists
 */
function ensureDir(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
  return dirPath;
}

/**
 * Read JSON file safely
 */
function readJSON(filePath, defaultValue = {}) {
  try {
    if (fs.existsSync(filePath)) {
      return JSON.parse(fs.readFileSync(filePath, 'utf8'));
    }
  } catch (e) {
    console.error(`Error reading ${filePath}:`, e.message);
  }
  return defaultValue;
}

/**
 * Write JSON file safely
 */
function writeJSON(filePath, data) {
  try {
    ensureDir(path.dirname(filePath));
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
    return true;
  } catch (e) {
    console.error(`Error writing ${filePath}:`, e.message);
    return false;
  }
}

/**
 * Get current working directory's .ai_state path
 */
function getAIStatePath() {
  return path.join(process.cwd(), AI_STATE_DIR);
}

/**
 * Generate unique session ID
 */
function generateSessionId() {
  const date = new Date().toISOString().split('T')[0];
  const random = Math.random().toString(36).substring(2, 10);
  return `${date}-${random}`;
}

/**
 * Get current timestamp in ISO format
 */
function timestamp() {
  return new Date().toISOString();
}

/**
 * Parse hook input from stdin
 */
async function parseHookInput() {
  return new Promise((resolve) => {
    let data = '';
    process.stdin.on('data', chunk => data += chunk);
    process.stdin.on('end', () => {
      try {
        resolve(JSON.parse(data));
      } catch {
        resolve({ raw: data });
      }
    });
  });
}

/**
 * Log with timestamp
 */
function log(message, level = 'info') {
  const prefix = {
    info: '[INFO]',
    warn: '[WARN]',
    error: '[ERROR]',
    hook: '[HOOK]'
  }[level] || '[LOG]';
  
  console.error(`${prefix} ${timestamp()} ${message}`);
}

module.exports = {
  HOME,
  CLAUDE_DIR,
  AI_STATE_DIR,
  ensureDir,
  readJSON,
  writeJSON,
  getAIStatePath,
  generateSessionId,
  timestamp,
  parseHookInput,
  log
};
