#!/usr/bin/env node
"use strict";

// Advanced Xring/Moonsec-style Obfuscation Detector
// Detects specific patterns and characteristics of commercial obfuscators

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class XringDetector {
  constructor() {
    this.techniques = {
      proprietaryEncoding: false,
      runtimeDecryption: false,
      antiDebug: false,
      controlFlow: false,
      stringEncryption: false,
      functionWrapping: false,
      bytecodePacker: false,
      saasProtection: false,
      antiTamper: false
    };
  }

  detect(code) {
    // Clear previous detection
    Object.keys(this.techniques).forEach(key => this.techniques[key] = false);

    this.analyzeArrays(code);
    this.analyzeDecryption(code);
    this.analyzeControlFlow(code);
    this.analyzeStringManipulation(code);
    this.analyzeAntiDebug(code);
    this.analyzePacking(code);
  }

  analyzeArrays(code) {
    // Look for large hex arrays (common in obfuscators)
    const hexArrayPattern = /\[\{dataset\}[%0-9A-Fa-f]+\]/g;
    const matches = code.match(hexArrayPattern);
    if (matches && matches.length > 2) {
      this.techniques.stringEncryption = true;
      this.techniques.proprietaryEncoding = true;
    }
  }

  analyzeDecryption(code) {
    // Look for decryption patterns
    const decryptPatterns = [
      /function\s+(__||_|\[|)\s*decrypt/gi,
      /local\s+decrypt\s*=\s*function\(/gi,
      /dofunction\(loadstring/gi,
      /load\([^()]+\)\(\)/gi,
    ];

    for (const pattern of decryptPatterns) {
      if (pattern.test(code)) {
        this.techniques.runtimeDecryption = true;
        break;
      }
    }
  }

  analyzeControlFlow(code) {
    // Look for obfuscated control flow
    const controlFlowPatterns = [
      /\bif\s*\([^)]+\)\s+then$/gm,
      /\belseif\s*\([^)]+\)\s+then$/gm,
      /\bdo/gm,
      /\b\w+\s*=\s*\w+\s*\(\s*\w+\s*\|\|\s*\w+\s*\+\s*1\s*\)/,
    ];

    let depth = 0;
    let maxDepth = 0;
    for (const char of code) {
      if (char === '{' || char === '(') depth++;
      if (char === '}' || char === ')') depth--;
      if (depth > maxDepth) maxDepth = depth;
    }

    if (maxDepth > 5) {
      this.techniques.controlFlow = true;
    }
  }

  analyzeStringManipulation(code) {
    // Look for string processing functions
    const stringPatterns = [
      /%[0-9a-fA-F]{2}/g, // Hex escapes
      /_G\[%[0-9a-fA-F]+\]|\["%[0-9a-fA-F]+"\]/g, // String indexing
      /string\.split\s*\(/g, // String splitting
      /string\.match\s*\([^)]*%[0-9]/gi, // Pattern matching
      /string\.format%s*\([^)]*%[xcX]/gi, // Format strings
    ];

    for (const pattern of stringPatterns) {
      if (pattern.test(code)) {
        this.techniques.stringEncryption = true;
        this.techniques.proprietaryEncoding = true;
        break;
      }
    }
  }

  analyzeAntiDebug(code) {
    // Look for anti-debugging methods
    const antiDebugPatterns = [
      /(?:debug|getfenv|getmetatable|setmetatable)\[?"[^"]*"?%]?\(?/gi,
      /debug\.hook[^;]+/gi,
      /pause\s*\(\)/gi,
      /(pcall|debug\.traceback|debug\.info)(\([^)]*\)|\s+)/g,
    ];

    for (const pattern of antiDebugPatterns) {
      if (pattern.test(code) && !pattern.test('//')) { // Exclude comments
        this.techniques.antiDebug = true;
        break;
      }
    }
  }

  analyzePacking(code) {
    // Look for packer signatures
    const packerSignatures = [
      /loadstring\s*suspend/g, // Common packer pattern
      /function\s+decrypt\s*\(.*?\)\s+wait/g, // Async decryption
      /\beval\s+load\(/, // Eval injection
      /string\.byte\s*-\s*127/g, // Range checking
    ];

    for (const signature of packerSignatures) {
      if (signature.test(code) && !signature.test('//')) {
        this.techniques.bytecodePacker = true;
        this.techniques.runtimeDecryption = true;
        break;
      }
    }
  }

  calculateSeverity() {
    const activeTechniques = Object.entries(this.techniques)
      .filter(([_, active]) => active)
      .map(([name]) => name);

    let severity = 0;
    const likelihoods = {
      runtimeDecryption: 30,
      antiDebug: 20,
      controlFlow: 15,
      stringEncryption: 15,
      functionWrapping: 10,
      bytecodePacker: 15,
      proprietaryEncoding: 10,
      saasProtection: 25,
      antiTamper: 25
    };

    for (const technique of activeTechniques) {
      severity += likelihoods[technique] || 10;
    }

    let riskLevel = 'LOW';
    if (severity > 45) riskLevel = 'HIGH';
    else if (severity > 25) riskLevel = 'MEDIUM';

    return {
      level: riskLevel,
      score: Math.min(100, severity),
      techniques: activeTechniques,
      detected: activeTechniques.length > 0
    };
  }

  getRecommendations(severity) {
    const recommendations = [];

    if (this.techniques.runtimeDecryption) {
      recommendations.push('⚠️  Runtime decryption detected - scan with sandbox environment');
    }

    if (this.techniques.antiDebug) {
      recommendations.push('✓ Anti-debugging mechanisms detected');
    }

    if (this.techniques.stringEncryption) {
      recommendations.push('🔍 String encryption patterns found - potential data hiding');
    }

    if (this.techniques.controlFlow) {
      recommendations.push('🔄 Complex control flow - use static analysis tools');
    }

    if (severity === 'HIGH') {
      recommendations.push('🔥 HIGH RISK: This code appears heavily obfuscated or packed');
      recommendations.push('💡 Isolate this file in a sandbox for analysis');
    }

    return recommendations;
  }
}

class CodeQuotientDifference {
  static calculate(code) {
    let letters = 0;
    let numbers = 0;
    let symbols = 0;
    let operators = 0;
    let whitespace = 0;

    for (const char of code) {
      if (/[a-zA-Z]/.test(char)) {
        letters++;
      } else if (/[0-9]/.test(char)) {
        numbers++;
      } else if (/[{}()\[\];,]/.test(char)) {
        symbols++;
      } else if (/[+\-*/=<>!&|^~%]/.test(char)) {
        operators++;
      } else if (/\s/.test(char)) {
        whitespace++;
      }
    }

    return {
      letters, numbers, symbols, operators, whitespace,
      quotient: symbols / (letters || 1),
      operatorDensity: operators / (letters + numbers || 1)
    };
  }
}

async function advancedDetect(filePath) {
  try {
    const detector = new XringDetector();
    const code = await fs.promises.readFile(filePath, 'utf-8');

    const rawAnalysis = detector.detect(code);
    const risk = detector.calculateSeverity();

    return {
      ...(await rawAnalysis),
      file: path.basename(filePath),
      size: code.length,
      codeQuotient: CodeQuotientDifference.calculate(code),
      recommendations: detector.getRecommendations(risk.level)
    };
  } catch (error) {
    console.error('Error analyzing file:', error.message);
    return null;
  }
}

async function sandboxedAnalysis(filePath) {
  try {
    // Try to use linter if available
    try {
      const luauts = execSync('luauts --help', { encoding: 'utf-8' });
      console.log('Luauts available - generating heuristic report');
    } catch (e) {
      console.log('Luauts not available - running heuristic analysis only');
    }

    return advancedDetect(filePath);
  } catch (error) {
    console.error('Analysis error:', error.message);
    return null;
  }
}

function displayAdvancedResult(result) {
  console.log('\n' + '='.repeat(70));
  console.log('XRING/MOONSEC-STYLE OBFUSCATION ANALYsis');
  console.log('='.repeat(70));
  console.log(`File: ${result.file}`);
  console.log(`Size: ${result.size} bytes`);
  console.log(`Risk Level: ${result.level}`);
  console.log(`Obfuscation Score: ${result.score}/100`);
  console.log('='.repeat(70));

  if (result.detected) {
    console.log('\n🚨 DETECTED OBFUSCATION TECHNIQUES:');
    result.techniques.forEach(tech => {
      console.log(`  ✓ ${tech.charAt(0).toUpperCase() + tech.slice(1)}`);
    });
  }

  console.log('\n📊 CODE CHARACTERISTICS:');
  const cq = result.codeQuotient;
  console.log(`  - Symbol Density: ${(cq.quotient * 100).toFixed(1)}%`);
  console.log(`  - Operator Density: ${(cq.operatorDensity * 100).toFixed(1)}%`);
  console.log(`  - Letters: ${cq.letters}`);
  console.log(`  - Numbers: ${cq.numbers}`);

  console.log('\n💡 ANALYSIS RECOMMENDATIONS:');
  result.recommendations.forEach(rec => {
    console.log(`  ${rec}`);
  });

  if (result.score >= 60) {
    console.log('\n🔥 CRITICAL: This exhibits characteristics of commercial obfuscators');
    console.log('   Recommended action: isolate in sandbox, analyze with behavioral monitoring');
  } else if (result.score >= 35) {
    console.log('\n⚠️  MEDIUM RISK: Consider extensive static analysis');
    console.log('   recommended action: use security tools, verify with trusted sources');
  }

  console.log('='.repeat(70) + '\n');
}

async function simulateDetection(content) {
  const detector = new XringDetector();
  detector.detect(content);
  return detector.calculateSeverity();
}

async function main() {
  const args = process.argv.slice(2);
  const filePath = args[0];

  if (!filePath) {
    console.log('Usage: node advanceddetector.js <file.lua>');
    console.log('Example: node advanceddetector.js malicious.lua');
    process.exit(1);
  }

  if (!fs.existsSync(filePath)) {
    console.error('File not found:', filePath);
    process.exit(1);
  }

  const result = await sandboxedAnalysis(filePath);
  if (result) {
    displayAdvancedResult(result);

    // Save to JSON if requested
    if (args.includes('-o')) {
      const outputIdx = args.indexOf('-o') + 1;
      const outputFile = args[outputIdx] || `'${filePath}_analysis.json'`;
      await fs.promises.writeFile(outputFile, JSON.stringify(result, null, 2));
      console.log(`Analysis saved to: ${outputFile}`);
    }
  }
}

main().catch(console.error);