"use strict";

// Module for obfuscation detection integration with the Discord bot

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

/**
 * Simple static analysis for obfuscation detection
 * Can be used within the bot to assess script risk
 */
class ObfuscationScanner {
  constructor() {
    this.techniques = {
      proprietaryEncoding: false,
      runtimeDecryption: false,
      antiDebug: false,
      stringEncryption: false,
      controlFlow: false,
      suspiciousImports: false
    };
  }

  /**
   * Scan Lua code for obfuscation patterns
   * @param {string} code - Lua code to analyze
   * @returns {Object} Detection results
   */
  scan(code, options = {}) {
    const { log = false } = options;

    // Reset detection state
    Object.keys(this.techniques).forEach(key => this.techniques[key] = false);

    // Store code for analysis
    this.code = code;

    this._detectPacking();
    this._detectRuntimeDecryption();
    this._detectStringEncryption();
    this._detectAntiDebug();
    this._detectControlFlow();
    this._detectSuspiciousImports();

    const risk = this._calculateRisk();

    if (log && risk.level === 'HIGH') {
      console.log(`[SCANNER] Obfuscated script detected: ${risk.score}%`);
    }

    return {
      riskLevel: risk.level,
      score: risk.score,
      techniques: Object.entries(this.techniques)
        .filter(([_, active]) => active)
        .map(([name]) => name),
      recommendations: this._getRecommendations(risk.level)
    };
  }

  _detectPacking() {
    const packerSignatures = [
      /\bloadstring\s+suspend/g,
      /dofunction\(loadstring/g,
      /function\s+hook\s*\(/,
    ];

    for (const pattern of packerSignatures) {
      if (pattern.test(this.code) && !pattern.test('//')) {
        this.techniques.proprietaryEncoding = true;
        this.techniques.runtimeDecryption = true;
        break;
      }
    }
  }

  _detectRuntimeDecryption() {
    const patterns = [
      /function\s+(__|d|_|\[)decrypt/gi,
      /loadstring\(.*?\)/,
      /dofunction\(loadstring/g,
      /local\s+decrypt\s*=\s*function\(/,
    ];

    for (const pattern of patterns) {
      if (pattern.test(this.code) && !pattern.test('//')) {
        this.techniques.runtimeDecryption = true;
        break;
      }
    }
  }

  _detectStringEncryption() {
    // Detect string encryption patterns
    const hasHexEscapes = /%[xX]/g.test(this.code);
    const hasHexCodes = /%[0-9A-Fa-f]+/g.test(this.code);
    const hasMultiChar = /%[^xX]/g.test(this.code);

    // Check for byte manipulation patterns
    if (hasHexEscapes && (hasHexCodes || hasMultiChar)) {
      this.techniques.stringEncryption = true;
    }

    // Check for custom byte array patterns
    if (this.code.includes('%[') || this.code.includes('%]')) {
      this.techniques.stringEncryption = true;
    }
  }

  _detectAntiDebug() {
    const patterns = [
      /debug\s*\./,
      /debug\.hook/,
      /pcall.*debug/,
    ];

    for (const pattern of patterns) {
      if (pattern.test(this.code) && !pattern.test('//')) {
        this.techniques.antiDebug = true;
        break;
      }
    }
  }

  _detectControlFlow() {
    // Look for excessive nesting
    const lines = this.code.split('\n');
    let maxNesting = 0;
    let currentNesting = 0;

    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('f') || trimmed.startsWith('l')) {
        currentNesting++;
      } else if (trimmed.startsWith('elseif') || trimmed.startsWith('else')) {
        currentNesting--;
      }

      if (currentNesting > maxNesting) maxNesting = currentNesting;
    }

    if (maxNesting > 4) this.techniques.controlFlow = true;
  }

  _detectSuspiciousImports() {
    const patterns = [
      /required/,
      /require\s*\(/,
    ];

    for (const pattern of patterns) {
      if (pattern.test(this.code) && !pattern.test('//')) {
        this.techniques.suspiciousImports = true;
        break;
      }
    }
  }

  _calculateRisk() {
    let score = 0;

    if (this.techniques.runtimeDecryption) score += 30;
    if (this.techniques.proprietaryEncoding) score += 20;
    if (this.techniques.antiDebug) score += 20;
    if (this.techniques.stringEncryption) score += 15;
    if (this.techniques.controlFlow) score += 15;
    if (this.techniques.suspiciousImports) score += 10;

    let level = 'LOW';
    if (score > 50) level = 'HIGH';
    else if (score > 25) level = 'MEDIUM';

    return { level, score };
  }

  _getRecommendations(level) {
    const recommendations = [];

    if (this.techniques.runtimeDecryption) {
      recommendations.push('Runtime decryption detected - requires sandboxed analysis');
    }

    if (this.techniques.antiDebug) {
      recommendations.push('Anti-debugging mechanisms present');
    }

    if (this.techniques.proprietaryEncoding) {
      recommendations.push('Proprietary/packed encoding detected');
    }

    if (level === 'HIGH') {
      recommendations.push('HIGH RISK: Consider isolating this script in a sandbox environment');
    }

    if (level === 'MEDIUM') {
      recommendations.push('MEDIUM RISK: Extended analysis recommended');
    }

    return recommendations;
  }
}

/**
 * Batch scan multiple files
 * @param {Array<string>} filePaths - Array of file paths to scan
 * @returns {Array<Object>} Scan results
 */
async function scanMultipleFiles(filePaths) {
  const results = [];
  const scanner = new ObfuscationScanner();

  for (const filePath of filePaths) {
    try {
      if (fs.statSync(filePath).isDirectory()) {
        const files = fs.readdirSync(filePath).filter(f => f.endsWith('.lua'));
        for (const file of files) {
          const code = fs.readFileSync(path.join(filePath, file), 'utf-8');
          const result = scanner.scan(code, { log: false });
          results.push({
            file: file,
            path: path.join(filePath, file),
            ...result
          });
        }
      } else {
        const code = fs.readFileSync(filePath, 'utf-8');
        const result = scanner.scan(code);
        results.push({
          file: path.basename(filePath),
          path: filePath,
          ...result
        });
      }
    } catch (error) {
      console.error(`Error scanning ${filePath}:`, error.message);
    }
  }

  return results;
}

/**
 * Generate human-friendly detection summary
 * @param {Object} scanResult - Scan result from scanner
 * @returns {string} Human-readable summary
 */
function generateSummary(scanResult) {
  const { riskLevel, score, techniques } = scanResult;
  const emoji = riskLevel === 'HIGH' ? '🔥' : riskLevel === 'MEDIUM' ? '⚠️' : '✅';

  let summary = `${emoji} Detection Result: ${riskLevel.toUpperCase()}\n`;
  summary += `  📊 Score: ${score}/100\n`;
  summary += `  🎯 Techniques detected: ${techniques.length > 0 ? 'Yes' : 'None'}\n`;

  return summary;
}

// Export for use in bot
module.exports = {
  ObfuscationScanner,
  scanMultipleFiles,
  generateSummary
};

// For command-line usage
if (require.main === module) {
  const args = process.argv.slice(2);

  if (!args.length || args.includes('-h') || args.includes('--help')) {
    console.log('Lua Obfuscation Scanner');
    console.log('\nUsage: node detector-utils.js [options] <file.lua>');
    console.log('\nOptions:');
    console.log('  -o, --output <file>   Save results to file');
    console.log('  -v, --verbose         Verbose output');
    console.log('  -m, --multiple <dir>  Scan all .lua files in directory');
    console.log('\nExample:');
    console.log('  node detector-utils.js script.lua');
    console.log('  node detector-utils.js -m ./scripts');
    process.exit(0);
  }

  const scanner = new ObfuscationScanner();

  const scanSingleFile = async (file) => {
    if (!fs.existsSync(file)) {
      console.error(`File not found: ${file}`);
      return;
    }

    console.log(`\n🔍 Scanning: ${file}`);
    const code = fs.readFileSync(file, 'utf-8');
    const result = scanner.scan(code);

    console.log(generateSummary(result));

    if (result.riskLevel === 'HIGH' && args.includes('-v')) {
      console.log(`\nDetected techniques:`);
      result.techniques.forEach(t => console.log(`  - ${t}`));
      console.log(`\nRecommendations:`);
      result.recommendations.forEach(r => console.log(`  ${r}`));
    }
  };

  if (args.includes('-m')) {
    const dirIdx = args.indexOf('-m') + 1;
    const dir = args[dirIdx];
    scanMultipleFiles([dir]).then(results => {
      results.forEach(result => {
        console.log(generateSummary(result));
        if (result.riskLevel === 'HIGH') {
          console.log(`  🔥 ${result.file}`);
        }
      });
    });
  } else {
    scanSingleFile(args[0]);
  }
}