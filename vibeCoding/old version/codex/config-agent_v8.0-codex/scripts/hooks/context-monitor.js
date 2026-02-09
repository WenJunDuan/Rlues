#!/usr/bin/env node
// VibeCoding Kernel v8.0 - Context Monitor Hook
// Monitors context window usage thresholds

// This hook is informational - actual context monitoring
// is handled by the smart-archive skill and server-side Compaction
console.error('[VibeCoding] Context monitor active. Thresholds: 200K/500K/800K');
