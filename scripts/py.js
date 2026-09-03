#!/usr/bin/env node
const { spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const root = path.resolve(__dirname, '..');
const venvWin = path.join(root, 'backend', 'venv', 'Scripts', 'python.exe');
const venvUnix = path.join(root, 'backend', 'venv', 'bin', 'python');

let py = 'python';
if (fs.existsSync(venvWin)) {
  py = venvWin;
} else if (fs.existsSync(venvUnix)) {
  py = venvUnix;
}

const args = process.argv.slice(2);
const result = spawnSync(py, args, {
  cwd: path.join(root, 'backend'),
  stdio: 'inherit',
  shell: true,
});

process.exit(result.status ?? 0);
