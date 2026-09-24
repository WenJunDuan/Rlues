#!/usr/bin/env node
/**
 * VibeCoding Kernel v7.9 - Session End Hook
 * Saves state and extracts patterns on session end
 */

const path = require('path');
const { 
  readJSON, 
  writeJSON, 
  ensureDir, 
  getAIStatePath,
  timestamp,
  log 
} = require('../lib/utils');

async function sessionEnd() {
  const aiState = getAIStatePath();
  const metaDir = path.join(aiState, 'meta');
  const sessionFile = path.join(metaDir, 'session.lock');
  
  // Load current session
  const session = readJSON(sessionFile, null);
  if (!session) {
    log('No active session found', 'warn');
    return;
  }
  
  // Update session
  session.ended = timestamp();
  session.active = false;
  session.duration = new Date(session.ended) - new Date(session.started);
  
  // Save session history
  const historyDir = path.join(aiState, 'meta', 'sessions');
  ensureDir(historyDir);
  const historyFile = path.join(historyDir, `${session.id}.json`);
  writeJSON(historyFile, session);
  
  // Clear active session
  writeJSON(sessionFile, { active: false, last_session: session.id });
  
  // Trigger pattern extraction if significant work done
  if (session.duration > 600000) { // > 10 minutes
    log('Session significant, triggering pattern extraction', 'info');
    // Pattern extraction would be triggered here
  }
  
  // Output summary
  console.log(JSON.stringify({
    session_id: session.id,
    duration_minutes: Math.round(session.duration / 60000),
    message: `Session ${session.id} ended`
  }));
  
  log(`Session ended: ${session.id} (${Math.round(session.duration / 60000)}min)`, 'hook');
}

sessionEnd().catch(e => {
  console.error('[ERROR]', e.message);
  process.exit(1);
});
