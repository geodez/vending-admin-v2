#!/usr/bin/env node

/**
 * Check that no /api/v1/api/v1 duplicates exist in the codebase.
 * This prevents accidental double-prefixing of API calls.
 * 
 * Also checks for patterns like '/v1/' at the start of paths,
 * which would cause duplication since baseURL already contains '/api/v1'.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const srcDir = path.join(__dirname, '..', 'src');
const checkString = '/api/v1/api/v1';

// Patterns that indicate incorrect API path usage
// These patterns would cause duplication since baseURL already contains '/api/v1'
const problematicPatterns = [
  /['"`]\/v1\//g,  // '/v1/', "/v1/", `/v1/`
  /['"`]\/api\/v1\/api\/v1\//g,  // Direct duplication
];

let hasErrors = false;
const errors = [];

function checkDirectory(dir) {
  const files = fs.readdirSync(dir);
  
  for (const file of files) {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    
    // Skip node_modules and other build directories
    if (file === 'node_modules' || file === '.git' || file === 'dist' || file === 'build') {
      continue;
    }
    
    if (stat.isDirectory()) {
      checkDirectory(filePath);
    } else if (file.endsWith('.ts') || file.endsWith('.tsx')) {
      try {
        const content = fs.readFileSync(filePath, 'utf-8');
        const relativePath = path.relative(process.cwd(), filePath);
        
        // Check for direct duplication
        if (content.includes(checkString)) {
          const lines = content.split('\n');
          lines.forEach((line, index) => {
            if (line.includes(checkString)) {
              errors.push({
                file: relativePath,
                line: index + 1,
                issue: `Found "${checkString}"`,
                code: line.trim()
              });
            }
          });
          hasErrors = true;
        }
        
        // Check for problematic patterns
        problematicPatterns.forEach((pattern, patternIndex) => {
          const matches = content.matchAll(pattern);
          for (const match of matches) {
            const lineNumber = content.substring(0, match.index).split('\n').length;
            const lines = content.split('\n');
            const line = lines[lineNumber - 1];
            
            // Skip if it's in a comment
            if (line.trim().startsWith('//') || line.includes('/*') || line.includes('*')) {
              continue;
            }
            
            // Skip if it's in baseURL definition (that's correct)
            if (line.includes('baseURL') || line.includes('VITE_API_BASE_URL')) {
              continue;
            }
            
            errors.push({
              file: relativePath,
              line: lineNumber,
              issue: `Found problematic pattern: ${match[0]} (would cause /api/v1/api/v1 duplication)`,
              code: line.trim()
            });
            hasErrors = true;
          }
        });
      } catch (err) {
        console.error(`Error reading file ${filePath}: ${err.message}`);
        hasErrors = true;
      }
    }
  }
}

console.log('🔍 Checking for API prefix duplicates in src/...');
checkDirectory(srcDir);

if (hasErrors) {
  console.error('\n❌ API prefix check failed!');
  console.error('\nFound issues:');
  errors.forEach((error, index) => {
    console.error(`\n${index + 1}. ${error.file}:${error.line}`);
    console.error(`   Issue: ${error.issue}`);
    console.error(`   Code: ${error.code}`);
  });
  console.error('\n❌ Fix these issues before building!');
  process.exit(1);
} else {
  console.log('✅ API prefix check passed!');
  process.exit(0);
}
