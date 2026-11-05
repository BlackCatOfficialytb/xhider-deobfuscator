#!/usr/bin/env node
"use strict";

// Lua Obfuscation Detection Tool
// Produces risk scores and detects common obfuscation patterns

const fs = require('fs');
const path = require('path');

const FLAGS = {
  v: { type: 'boolean', name: 'verbose', desc: 'Enable verbose output' },
  i: { type: 'boolean', name: 'interactive', desc: 'Interactive mode (prompt for input)' },
  o: { type: 'string', name: 'output', desc: 'Output file for results (JSON)' }
};

class ObfuscationDetector {
  constructor() {
    this.risks = [];
    this.stats = {};
  }

  addRisk(severity, category, message, codeContext = null) {
    this.risks.push({ severity, category, message, codeContext });
  }

  detectTypes(code) {
    const stats = {
      strings: 0,
      functions: 0,
      comments: 0,
      controlFlow: 0,
      stringEncoding: new Set(),
      selfModifying: false,
      suspiciousImports: [],
      variableNameLength: [],
      globalVars: new Set()
    };

    // Remove comments first for detection
    const codeWithoutComments = code.replace(/--\[=*\[([\s\S]*?)%-=*\]/g, '');
    const lines = codeWithoutComments.split('\n');

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmed = line.trim();

      if (!trimmed) continue;

      // Comment detection
      if (trimmed.startsWith('--') || trimmed.match(/--\[=*\[/)) {
        stats.comments++;
        continue;
      }

      // Function detection
      if (trimmed.match(/\b(function|local function)\s+\w+/)) {
        stats.functions++;
      }

      // Variable references
      if (trimmed.match(/\blocal\s+\w+/)) {
        const match = trimmed.match(/local\s+(\w+)\s*=/);
        if (match) {
          stats.variableNameLength.push(match[1].length);
        }
      }

      if (trimmed.includes('= ')) {
        const match = trimmed.match(/(\w+)\s*=/);
        if (match && match[1] !== 'local') {
          stats.globalVars.add(match[1]);
        }
      }

      // String detection
      if (trimmed.match(/["']((?:(?!\1)\\.|.)*?)["']/)) {
        stats.strings++;

        // Detect string encoding patterns
        if (trimmed.match(/%[xX][0-9A-Fa-f]+/)) {
          stats.stringEncoding.add('Hex');
        }
        if (trimmed.match(/%[uU][0-9]/)) {
          stats.stringEncoding.add('Unicode');
        }
        if (trimmed.match(/\[[%0-9a-fA-F]+\]/)) {
          stats.stringEncoding.add('ByteArray');
        }
      }

      // Control flow detection
      if (trimmed.match(/\b(if|then|else|elseif|while|for|repeat|until|do|break|return)\s+/)) {
        stats.controlFlow++;
      }

      // Self-modifying code detection
      if (trimmed.match(/\b(load|string\.byte|string\.char|string\.find|string\.match|string\.gmatch|string\.gsub)\b/)) {
        stats.selfModifying = true;
      }

      // Suspicious imports
      if (trimmed.match(/\b(loadfile|dofile|require|loadstring|getfenv|setfenv)\b/)) {
        stats.suspiciousImports.push(trimmed.substring(0, 100));
      }

      // String manipulation patterns
      if (trimmed.match(/\bsplit\s*\(/) || trimmed.match(/\bconcat\s*\(/) || trimmed.match(/\bsub\s*\(/)) {
        stats.stringEncoding.add('Manipulation');
      }

      // Base64 detection
      if (trimmed.match(/\bbase64|unpack(%s*,)/)) {
        stats.stringEncoding.add('Base64');
      }

      // Cryptic variable names
      if (trimmed.match(/\b[a-z]{2,3}\s*(?=[(),=\+\-\*/])/)) {
        stats.stringEncoding.add('ShortVars');
      }
    }

    this.stats = stats;
  }

  calculateRisk() {
    let riskScore = 0;
    const details = [];

    // Risk factors
    if (this.stats.comments > 0 && this.stats.functions > this.stats.comments * 3) {
      riskScore += 15;
      this.addRisk('medium', 'Code Structure', 'High function-to-comment ratio suggests obfuscation');
    }

    if (this.stats.selfModifying) {
      riskScore += 20;
      this.addRisk('high', 'Self-modifying', 'Uses string manipulation functions (self-modifying code detected)');
    }

    if (this.stats.suspiciousImports.length > 0) {
      riskScore += 25;
      this.addRisk('high', 'Suspicious Imports', 'Uses dangerous runtime functions');
    }

    if (this.stats.stringEncoding.size >= 4) {
      riskScore += 15;
      this.addRisk('medium', 'String Encoding', 'Uses multiple encoding techniques');
    }

    if (this.stats.globalVars.size > 10) {
      riskScore += 10;
      this.addRisk('low', 'Code Structure', 'Many global variables');
    }

    // Look for specific obfuscation patterns
    stringPatterns.forEach(pattern => {
      if (pattern.regex.test(this.stats.code)) {
        riskScore += pattern.score;
        this.addRisk(pattern.severity, pattern.category, pattern.message);
      }
    });

    // Calculate obfuscation likelihood
    const obfuscationScore = Math.min(100, riskScore);

    return {
      riskLevel: riskScore > 50 ? 'HIGH' : riskScore > 25 ? 'MEDIUM' : 'LOW',
      obfuscationScore,
      risks: this.risks,
      stats: this.stats
    };
  }
}

const stringPatterns = [
  {
    name: 'Func Wrapping',
    severity: 'medium',
    category: 'Code Structure',
    score: 10,
    message: 'Obfuscated function definitions detected',
    regex: /\beval\s*\(.*?\)/i
  },
  {
    name: 'Code Injection',
    severity: 'high',
    category: 'Security',
    score: 25,
    message: 'Uses eval/loadstring - potential code injection risk',
    regex: /\beval\s*\(.*?\)/i
  },
  {
    name: 'Byte Generation',
    severity: 'medium',
    category: 'Obfuscation',
    score: 10,
    message: 'Byte code generation pattern detected',
    regex: /string\.byte.*string\.char/gi
  },
  {
    name: 'Control Flow',
    severity: 'low',
    category: 'Code Structure',
    score: 5,
    message: 'Complex control flow detected',
    regex: /\bif.*then\s+(else|elseif)/g
  },
  {
    name: 'Reverse Engineering',
    severity: 'medium',
    category: 'Obfuscation',
    score: 15,
    message: 'Pattern suggests anti-debugging attempts',
    regex: /\bdebug\s*\.\s*\w+/gi
  },
  {
    name: 'Memory Operations',
    severity: 'high',
    category: 'Security',
    score: 20,
    message: 'Direct memory operations detected',
    regex: /\bstring\.sub\s*\([^,]*,\s*-?\d+\)/gi
  }
];

async function analyzeFile(filePath) {
  try {
    const detector = new ObfuscationDetector();
    const code = await fs.promises.readFile(filePath, 'utf-8');
    detector.stats.code = code;

    detector.detectTypes(code);
    const result = detector.calculateRisk();

    result.fileName = path.basename(filePath);
    result.fileSize = code.length;
    result.filePath = path.resolve(filePath);

    return result;
  } catch (error) {
    console.error(`Error analyzing ${filePath}:`, error.message);
    return null;
  }
}

async function analyzeString(code) {
  const detector = new ObfuscationDetector();
  detector.stats.code = code;
  detector.detectTypes(code);
  return detector.calculateRisk();
}

function displayResult(result) {
  console.log('\n' + '='.repeat(60));
  console.log('OBFUSCATION DETECTION REPORT');
  console.log('='.repeat(60));
  console.log(`File: ${result.fileName}`);
  console.log(`Size: ${result.fileSize} bytes`);
  console.log(`Risk Level: ${result.riskLevel}`);
  console.log(`Obfuscation Score: ${result.obfuscationScore}/100`);
  console.log('='.repeat(60));

  if (result.risks.length > 0) {
    console.log('\nDETECTED RISKS:');
    result.risks.forEach((risk, i) => {
      console.log(`\n[${i + 1}] ${risk.category} (${risk.severity.toUpperCase()})`);
      console.log(`    ${risk.message}`);
    });
  }

  if (result.stats.strings > 0) {
    console.log('\nCODE STATISTICS:');
    console.log(`  - Comments: ${result.stats.comments}`);
    console.log(`  - Functions: ${result.stats.functions}`);
    console.log(`  - String Encodings: ${Array.from(result.stats.stringEncoding).join(', ') || 'None'}`);
    console.log(`  - Self-Modifying: ${result.stats.selfModifying}`);
    console.log(`  - Control Flow Statements: ${result.stats.controlFlow}`);
    console.log(`  - Suspicious Imports: ${result.stats.suspiciousImports.length}`);
  }

  if (result.obfuscationScore >= 50) {
    console.log('\n⚠️  HIGH RISK: This code appears heavily obfuscated!');
  } else if (result.obfuscationScore >= 25) {
    console.log('\n⚠️  MEDIUM RISK: Some obfuscation patterns detected');
  }
  console.log('='.repeat(60) + '\n');
}

async function main() {
  // Parse arguments
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.log('Usage: node detectobfuscation.js <file.lua> [options]');
    console.log('Options:');
    console.log('  -v, --verbose      Enable verbose output');
    console.log('  -i, --interactive  Interactive mode');
    console.log('  -o, --output <file>  Save results to JSON file');
    process.exit(1);
  }

  const firstArg = args[0];
  const isPath = fs.existsSync(firstArg) && path.extname(firstArg) === '.lua';

  if (isPath) {
    const result = await analyzeFile(firstArg);
    if (result) {
      displayResult(result);

      // Save to output if specified
      if (args.includes('-o') || args.includes('--output')) {
        const outputIdx = args.indexOf('-o') >= 0 ? 3 : args.indexOf('--output') + 1;
        const outputFile = args[outputIdx];
        await fs.promises.writeFile(
          outputFile,
          JSON.stringify(result, null, 2),
          'utf-8'
        );
        console.log(`Results saved to ${outputFile}`);
      }
    }
  } else {
    // String analysis mode
    const code = firstArg;
    if (args.includes('-i') || args.includes('--interactive')) {
      console.log('Enter Lua code to analyze (Ctrl+D or Ctrl+Z to finish):');
      const inputCode = [];
      for await (const chunk of require('get-stdin-promise')) {
        inputCode.push(chunk);
      }
      const analyzedCode = inputCode.join('');
      const result = await analyzeString(analyzedCode);
      displayResult(result);
    } else {
      const result = await analyzeString(code);
      displayResult(result);
    }
  }
}

main().catch(console.error);