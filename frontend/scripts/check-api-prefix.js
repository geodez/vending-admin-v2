#!/usr/bin/env node

/**
 * Check that no /api/v1/api/v1 duplicates exist in the codebase.
 * This prevents accidental double-prefixing of API calls.
 */

const fs = require('fs');
const path = require('path');

const apiDir = path.join(__dirname, '..', 'src', 'api');
const checkString = '/api/v1/api/v1';

let hasErrors = false;

function checkDirectory(dir) {
  const files = fs.readdirSync(dir);
  
  for (const file of files) {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    
    if (stat.isDirectory()) {
      checkDirectory(filePath);
    } else if (file.endsWith('.ts') || file.endsWith('.tsx')) {
      try {
        const content = fs.readFileSync(filePath, 'utf-8');
        
        if (content.includes(checkString)) {
          console.error(`❌ Found "${checkString}" in ${path.relative(process.cwd(), filePath)}`);
          hasErrors = true;
        }
      } catch (err) {
        console.error(`Error reading file ${filePath}: ${err.message}`);
        hasErrors = true;
      }
    }
  }
}

console.log('🔍 Checking for API prefix duplicates...');
checkDirectory(apiDir);

if (hasErrors) {
  console.error('\n❌ API prefix check failed!');
  process.exit(1);
} else {
  console.log('✅ API prefix check passed!');
  process.exit(0);
}
