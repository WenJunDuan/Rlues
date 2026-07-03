#!/usr/bin/env node
/**
 * VibeCoding Kernel v7.9 - Session Start Hook
 * Loads context and state on session start
 */

const path = require('path');
const { 
  readJSON, 
  writeJSON, 
  ensureDir, 
  getAIStatePath, 
  generateSessionId,
  timestamp,
  log 
} = require('../lib/utils');

async function sessionStart() {
  const aiState = getAIStatePath();
  const metaDir = path.join(aiState, 'meta');
  ensureDir(metaDir);
  
  // Generate session ID
  const sessionId = generateSessionId();
  const sessionFile = path.join(metaDir, 'session.lock');
  
  // Check for existing session
  const existingSession = readJSON(sessionFile, null);
  if (existingSession && existingSession.active) {
    log(`Previous session found: ${existingSession.id}`, 'warn');
    log('Recovering state...', 'info');
  }
  
  // Create new session
  const session = {
    id: sessionId,
    started: timestamp(),
    active: true,
    cwd: process.cwd(),
    context: {
      instincts_loaded: 0,
      experience_loaded: 0,
      knowledge_loaded: 0
    }
  };
  
  // Load instincts
  const instinctsFile = path.join(aiState, 'instincts', 'instincts.json');
  const instincts = readJSON(instinctsFile, { instincts: [] });
  session.context.instincts_loaded = instincts.instincts?.length || 0;
  
  // Load experience index
  const experienceIndex = path.join(aiState, 'experience', 'index.md');
  if (require('fs').existsSync(experienceIndex)) {
    session.context.experience_loaded = 1;
  }
  
  // Save session
  writeJSON(sessionFile, session);
  
  // Output for Claude
  console.log(JSON.stringify({
    session_id: sessionId,
    context: session.context,
    message: `Session ${sessionId} started`
  }));
  
  log(`Session started: ${sessionId}`, 'hook');
  log(`Loaded: ${session.context.instincts_loaded} instincts`, 'info');
}

sessionStart().catch(e => {
  console.error('[ERROR]', e.message);
  process.exit(1);
});
