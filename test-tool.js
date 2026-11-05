#!/usr/bin/env node
"use strict";

// Test script for obfuscation detection tools
// Run this to demonstration how the detection works

const fs = require('fs');
const { generateSummary } = require('./detector-utils');

const TEST_CASES = [
  {
    name: 'Clean Lua Script',
    code: `-- Helper function
local function add(x, y)
  return x + y
end

-- Main execution
print("Starting...")
local result = add(5, 3)
print("Result: " .. tostring(result))`,
    expectedRisk: 'LOW'
  },
  {
    name: 'Simple Obfuscation',
    code: `-- Obfuscated
local _ = function() return loadstring ??? end
local __ = decodeString function
local consolelog = gmatch`,
    expectedRisk: 'MEDIUM'
  },
  {
    name: 'Xring-style Patterns',
    code: `-- Xring/Moonsec simulation
local _Stage1 = {
  [0] = 102,[110],
  [0] = 101],
  [0] = 102]
}

local function decodeString(encoded)
  local result = ""
  local j = 1

  for i = 1, #encoded do
    local char = encoded:sub(i, i)
    if char == '%' then
      local charCode = tonumber(encoded:sub(i+1, i+2), 16)
      result = result .. string.char(charCode)
    end
  end

  return result
end

local code = "local Player = game:GetService('Players'):LocalPlayer;"
local decrypted = decodeString(code)

-- Anti-debugging
local isDebuggerAttached = false
if debug.getenv then
  isDebuggerAttached = true
end

if isDebuggerAttached then
  return nil
end

loadstring(decrypted)()`,
    expectedRisk: 'HIGH'
  }
];

runTests().then(() => {
  console.log('\n✓ All tests completed successfully!');
}).catch(error => {
  console.error('\n✗ Test failed:', error.message);
  process.exit(1);
});

async function runTests() {
  const ObfuscationScanner = require('./detector-utils').ObfuscationScanner;

  console.log('\n🧪 Running Obfuscation Detection Tests');
  console.log('='.repeat(70));

  for (const testCase of TEST_CASES) {
    console.log(`\n📝 Test Case: ${testCase.name}`);
    console.log('-'.repeat(70));

    const code = testCase.code;
    const codeScanner = new ObfuscationScanner();
    const result = codeScanner.scan(code, { log: false });

    console.log(generateSummary(result));

    if (result && result.techniques && result.techniques.length > 0) {
      console.log(`\n  🎯 Detected Techniques (${result.techniques.length}):`);
      result.techniques.forEach(tech => {
        console.log(`     • ${tech}`);
      });
    }

    if (result && result.recommendations && result.recommendations.length > 0) {
      console.log(`\n  💡 Recommendations:`);
      result.recommendations.forEach(rec => {
        console.log(`     ${rec}`);
      });
    }

    // Check if expected risk matches
    if (result && result.riskLevel === testCase.expectedRisk) {
      console.log(`\n  ✅ Risk level matched: ${testCase.expectedRisk.toUpperCase()}`);
    } else {
      console.log(`\n  ⚠️  Risk level mismatch: Expected ${testCase.expectedRisk.toUpperCase()}, got ${result?.riskLevel?.toUpperCase() || 'UNKNOWN'}`);
    }
  }

  console.log('\n' + '='.repeat(70));
  console.log('📊 Test Summary');
  console.log('='.repeat(70));

  const totalRiskLevel = {};
  TEST_CASES.forEach(tc => {
    const resultScanner = new ObfuscationScanner();
    const result = resultScanner.scan(tc.code, { log: false });
    totalRiskLevel[result.riskLevel] = (totalRiskLevel[result.riskLevel] || 0) + 1;
  });

  console.log('Risk Level Distribution:');
  for (const [level, count] of Object.entries(totalRiskLevel)) {
    const emoji = level === 'HIGH' ? '🔥' : level === 'MEDIUM' ? '⚠️' : '✅';
    console.log(`  ${emoji} ${level.toUpperCase()}: ${count}/${TEST_CASES.length}`);
  }

  console.log('\n✓ Test suite completed');
}