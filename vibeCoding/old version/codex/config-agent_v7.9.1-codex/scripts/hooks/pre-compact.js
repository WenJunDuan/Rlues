#!/usr/bin/env node
/**
 * VibeCoding Kernel v7.9 - Pre-Compact Hook
 * Saves state before context compaction
 */

const path = require('path');
const { 
  readJSON, 
  writeJSON, 
  ensureDir, 
  getAIStatePath,
  timestamp,
  parseHookInput,
  log 
} = require('../lib/utils');

async function preCompact() {
  const input = await parseHookInput();
  const aiState = getAIStatePath();
  
  // Create pre-compact state
  const preCompactState = {
    timestamp: timestamp(),
    trigger: input.trigger || 'manual',
    context_usage: input.context_usage || 'unknown',
    
    // Current task state
    active_task: input.task_id || null,
    task_phase: input.phase || null,
    
    // Files being worked on
    active_files: input.active_files || [],
    
    // Pending work
    pending_todos: input.pending_todos || [],
    
    // Important context to preserve
    key_decisions: input.decisions || [],
    
    // Recovery instructions
    resume_hint: input.resume_hint || 'Continue from last checkpoint'
  };
  
  // Save pre-compact state
  const stateFile = path.join(aiState, 'meta', 'pre-compact-state.yaml');
  ensureDir(path.dirname(stateFile));
  
  // Write as YAML-like format for readability
  const yamlContent = `# Pre-Compact State
# Saved: ${preCompactState.timestamp}
# Trigger: ${preCompactState.trigger}

active_task: ${preCompactState.active_task || 'none'}
task_phase: ${preCompactState.task_phase || 'none'}
context_usage: ${preCompactState.context_usage}

active_files:
${preCompactState.active_files.map(f => `  - ${f}`).join('\n') || '  - none'}

pending_todos:
${preCompactState.pending_todos.map(t => `  - ${t}`).join('\n') || '  - none'}

key_decisions:
${preCompactState.key_decisions.map(d => `  - ${d}`).join('\n') || '  - none'}

resume_hint: |
  ${preCompactState.resume_hint}
`;

  require('fs').writeFileSync(stateFile, yamlContent);
  
  // Also save JSON version for programmatic access
  writeJSON(path.join(aiState, 'meta', 'pre-compact-state.json'), preCompactState);
  
  console.log(JSON.stringify({
    saved: true,
    file: stateFile,
    message: 'Pre-compact state saved'
  }));
  
  log('Pre-compact state saved', 'hook');
}

preCompact().catch(e => {
  console.error('[ERROR]', e.message);
  process.exit(1);
});
