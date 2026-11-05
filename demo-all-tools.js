#!/usr/bin/env node
"use strict";

// Comprehensive demonstration of the obfuscation detection suite
// Shows integration between all detection tools

const fs = require('fs');
const path = require('path');
const { ObfuscationScanner, generateSummary } = require('./detector-utils');

console.log('╔══════════════════════════════════════════════════════════════╗');
console.log('║     🛡️  OBFUSCATION DETECTION SUITE - COMPREHENSIVE DEMO   ║');
console.log('╚══════════════════════════════════════════════════════════════╝\n');

// Sample code profiles
const samples = {
  clean: {
    name: 'Clean Lua Code',
    code: `-- Example clean Lua script
function calculateSum(numbers)
  local total = 0
  for _, num in ipairs(numbers) do
    total = total + num
  end
  return total
end

-- Example usage
local result = calculateSum({1, 2, 3, 4, 5})
print("Sum: " .. result)
`
  },

  simpleObf: {
    name: 'Simple Obfuscation',
    code: `-- Custom variable names only
local _a = 10
local _b = 20
local _c = _a + _b

-- Conditional logic
if _c > 25 then
  print("Greater")
else
  print("Less")
end
`
  },

  xring: {
    name: 'Xring-style Obfuscation',
    code: `-- Xring-style patterns
local _123 = {
  [0] = 33,  [1] = 99, [2] = 119,
  [3] = 32,  [4] = 46, [5] = 100,
  _Library = {}
}

local function decrypt_data(data, key)
  local decoded = ""
  local idx = 1

  for i = 1, #data do
    local code = string.byte(data:sub(i, i))

    if code >= 65 and code <= 90 then
      decoded = decoded .. string.char(code + key)
    elseif code >= 97 and code <= 122 then
      decoded = decoded .. string.char(code + key)
    end
  end

  return decoded
end

local function check_debug()
  local hook = debug.gethook()
  if hook then
    return true
  end
  return false
end

-- Execution
if not check_debug() then
  local encrypted = "Hello World"
  local decrypted = decrypt_data(encrypted, 1)
  print(decrypted)
end
`
  },

  commercial: {
    name: 'Commercial Packer',
    code: `-- Heavy commercial packer patterns
__G = loadstring or error
_G.deobfuscate = function()
  -- Deeply nested structures
  local function ____(module)
    local _ = {}

    _.__ = function()
      local result = eval(function()
        -- Custom encoding
        local charSets = {
          "[   ]",
          "_   _",
          "camCam"
        }

        -- String manipulation
        local processed = {}
        -- ... advanced patterns
      end)

      return result
    end

    return _
  end

  return ____()
end

-- Runtime execution
local script = _G.deobfuscate()()
`
  }
};

// Demo: Parallel processing
console.log('📊 RUN 1: Parallel Analysis of All Samples\n');
console.log('═'.repeat(70));

const scanner = new ObfuscationScanner();

async function analyzeAllSamples() {
  const results = [];

  for (const [key, sample] of Object.entries(samples)) {
    const detectionResult = scanner.scan(sample.code, { log: false });
    const summary = generateSummary(detectionResult);
    const riskMatch = summary.match(/Detection Result: (\w+)/);
    const riskLevel = riskMatch ? riskMatch[1] : 'LOW';

    results.push({
      name: sample.name,
      key,
      summary,
      riskLevel,
      techniques: detectionResult
    });
  }

  return results;
}

// Demo: Risk Assessment Workflow
async function demoRiskWorkflow(input) {
  console.log('\n🎯 RUN 2: Risk Assessment Workflow\n');
  const result = scanner.scan(input.code, { log: true });
  const summary = generateSummary(result);

  console.log(summary);

  // Decision tree
  console.log('\n📋 DECISION TRAJECTORY:');
  if (result.riskLevel === 'HIGH') {
    console.log('  🔥 ACTION: BLOCK IMMEDIATELY');
    console.log('  🎯 REASON: Multiple risk factors detected');
    console.log('  🔍 RECOMMENDATION: Isolate in sandbox for behavioral analysis');
  } else if (result.riskLevel === 'MEDIUM') {
    console.log('  ⚠️  ACTION: REQUIRES MANUAL REVIEW');
    console.log('  🎯 REASON: Suspicious patterns but not clearly malicious');
    console.log('  🔍 RECOMMENDATION: Inspect source code manually');
  } else {
    console.log('  ✅ ACTION: APPROVE WITH MONITORING');
    console.log('  🎯 REASON: Code appears clean');
    console.log('  🔍 RECOMMENDATION: Continue with normal processing');
  }

  return result;
}

// Demo: Technical Breakdown
async function demoTechnicalAnalysis(sample) {
  console.log('\n🔬 RUN 3: Technical Detail Analysis\n');
  const result = scanner.scan(sample.code, { log: false });

  console.log('DETECTED CHARACTERISTICS:\n');

  if (result.techniques && result.techniques.length > 0) {
    console.log('Obfuscation Techniques:');
    result.techniques.forEach((tech, i) => {
      const emoji = tech.includes('Runtime') ? '🔧' : tech.includes('Anti') ? '🛡️' : '📦';
      console.log(`  ${emoji} ${i + 1}. ${tech}`);
    });
  } else {
    console.log('  ✅ No obfuscation techniques detected');
  }

  console.log('\nRECOMMENDATIONS:');
  if (result.recommendations && result.recommendations.length > 0) {
    result.recommendations.forEach((rec, i) => {
      console.log(`  ${i + 1}. ${rec}`);
    });
  } else {
    console.log('  None required');
  }
}

// Demo: Integration Example
async function demoBotIntegration() {
  console.log('\n🔥 RUN 4: Discord Bot Integration Example\n');
  const fakeUserScript = samples.xring.code;

  // Simulate bot processing
  console.log('simulating Discord bot receiving user script...\n');

  const result = scanner.scan(fakeUserScript, { log: true });

  // Bot response logic
  const botResponse = generateBotResponse(result);
  console.log(botResponse);

  return result;
}

function generateBotResponse(result) {
  const RISK_EMOJIS = { HIGH: '🚨', MEDIUM: '⚠️', LOW: '✅' };

  const emoji = RISK_EMOJIS[result.riskLevel];

  let response = `**${emoji} DEObfuscation Analysis Result**\n\n`;
  response += `**Risk Level:** ${result.riskLevel.toUpperCase()}\n`;
  response += `**Score:** ${result.score}/100\n`;
  response += `**Detected Techniques:** ${result.techniques?.length || 0}\n\n`;

  if (result.riskLevel === 'HIGH') {
    response += '**🚨 SECURITY ACTION REQUIRED**\n\n';
    response += 'This script exhibits multiple obfuscation patterns commonly used in\n';
    response += 'malicious code. It is recommended to:\n\n';
    response += '• BLOCK immediate execution\n';
    response += '• Isolate in sandbox environment\n';
    response += '• Require administrator approval';
  } else if (result.riskLevel === 'MEDIUM') {
    response += '**⚠️ REVIEW REQUIRED**\n\n';
    response += 'This script shows some suspicious patterns. Before execution:\n\n';
    response += '• Manually inspect the code\n';
    response += '• Verify source reputation\n';
    response += '• Consider additional analysis';
  } else {
    response += '**✅ SAFE PROCESSING**\n\n';
    response += 'This script appears clean. Proceed with caution as always.\n';
    response += 'Consider additional testing if the code is from an unknown source.';
  }

  return response;
}

// Run all demos
async function runAllDemos() {
  try {
    // Demo 1: Parallel analysis
    const results = await analyzeAllSamples();

    console.log('\n' + '═'.repeat(70));
    console.log('📊 PARALLEL ANALYSIS COMPLETED');
    console.log('═'.repeat(70));

    results.forEach(result => {
      const status = result.riskLevel === 'HIGH' ? '🔥' : result.riskLevel === 'MEDIUM' ? '⚠️' : '✅';
      console.log(`\n${status} ${result.name}: ${result.riskLevel.toUpperCase()} (${result.summary.match(/Score: \d+\/100/)} )`);
    });

    // Demo 2: Risk workflow
    await demoRiskWorkflow(samples.simpleObf);

    // Demo 3: Technical analysis
    await demoTechnicalAnalysis(samples.commercial);

    // Demo 4: Bot integration
    await demoBotIntegration();

    // Summary
    console.log('\n' + '═'.repeat(70));
    console.log('📚 DEMONSTRATION COMPLETE');
    console.log('═'.repeat(70));
    console.log('\nKey Takeaways:\n');
    console.log('1. Multiple detection tools provide comprehensive coverage');
    console.log('2. Risk assessment should use decision trees not automatic blocking');
    console.log('3. Integration with bots requires careful response generation');
    console.log('4. Always consider context and user reputation');

  } catch (error) {
    console.error('Demo Error:', error.message);
    process.exit(1);
  }
}

// Run the demonstration
runAllDemos().then(() => {
  console.log('\n✨ All demonstrations completed successfully!\n');
  process.exit(0);
}).catch(error => {
  console.error('\n❌ Demonstration failed:', error);
  process.exit(1);
});