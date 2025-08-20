/**
 * Clean script for PropertyAI Mobile App
 * Cross-platform compatible cleanup script
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT_DIR = path.resolve(__dirname, '..');

console.log('🧹 Cleaning up project files...');

// Directories to remove
const dirsToRemove = [
  path.join(ROOT_DIR, 'node_modules'),
  path.join(ROOT_DIR, '.expo'),
];

// Files to remove
const filesToRemove = [
  path.join(ROOT_DIR, 'package-lock.json'),
  path.join(ROOT_DIR, 'yarn.lock'),
];

// Remove directories
dirsToRemove.forEach(dir => {
  if (fs.existsSync(dir)) {
    console.log(`Removing directory: ${path.relative(ROOT_DIR, dir)}`);
    try {
      fs.rmSync(dir, { recursive: true, force: true });
    } catch (err) {
      console.error(`Error removing ${dir}:`, err);
    }
  }
});

// Remove files
filesToRemove.forEach(file => {
  if (fs.existsSync(file)) {
    console.log(`Removing file: ${path.relative(ROOT_DIR, file)}`);
    try {
      fs.unlinkSync(file);
    } catch (err) {
      console.error(`Error removing ${file}:`, err);
    }
  }
});

// Clean npm cache
console.log('Cleaning npm cache...');
try {
  execSync('npm cache clean --force', { stdio: 'inherit' });
} catch (err) {
  console.error('Error cleaning npm cache:', err);
}

console.log('✅ Cleanup complete!');