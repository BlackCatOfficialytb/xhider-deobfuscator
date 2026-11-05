#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for obfuscation detection tools
Run this to validate the detection works correctly
"""

import sys
import json
from pathlib import Path

from detector_utils import ObfuscationScanner, generate_summary

# Sample test cases
TEST_CASES = [
    {
        'name': 'Clean Lua Script',
        'code': '''-- Helper function
local function add(x, y)
  return x + y
end

-- Main execution
print("Starting...")
local result = add(5, 3)
print("Result: " .. tostring(result))''',
        'expectedRisk': 'LOW'
    },
    {
        'name': 'Simple Obfuscation',
        'code': '''-- Obfuscated
local _ = function() return loadstring ??? end
local __ = decodeString function
local consolelog = gmatch''',
        'expectedRisk': 'MEDIUM'
    },
    {
        'name': 'Xring-style Patterns',
        'code': '''-- Xring/Moonsec simulation
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
    if char == "%" then
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

loadstring(decrypted)()''',
        'expectedRisk': 'HIGH'
    }
]


def run_tests():
    """Run the test suite"""

    print('\n🧪 Running Obfuscation Detection Tests')
    print('=' * 70)

    total_tests = 0
    passed_tests = 0
    results = []

    for test_case in TEST_CASES:
        print(f'\n📝 Test Case: {test_case["name"]}')
        print('-' * 70)

        code = test_case['code']
        scanner = ObfuscationScanner()
        result = scanner.scan(code, log=False)

        print(generate_summary(result))

        techniques = result.get('techniques', [])
        if techniques:
            print(f'\n  🎯 Detected Techniques ({len(techniques)}):')
            for tech in techniques:
                print(f'     • {tech}')

        recommendations = result.get('recommendations', [])
        if recommendations:
            print(f'\n  💡 Recommendations:')
            for rec in recommendations:
                print(f'     {rec}')

        # Check if expected risk matches
        expected_risk = test_case['expectedRisk']
        actual_risk = result['riskLevel']

        is_risk_correct = (actual_risk == expected_risk)
        total_tests += 1

        if is_risk_correct:
            print(f'\n  ✅ Risk level matched: {expected_risk.upper()}')
            passed_tests += 1
        else:
            print(f'\n  ⚠️  Risk level mismatch: Expected {expected_risk.upper()}, got {actual_risk.upper()}')

        results.append({
            'test_name': test_case['name'],
            'expected_risk': expected_risk,
            'actual_risk': actual_risk,
            'risk_correct': is_risk_correct,
            'score': result['score'],
            'techniques': techniques
        })

    # Test Summary
    print('\n' + '=' * 70)
    print('📊 Test Summary')
    print('=' * 70)

    risk_counts = {}
    for result in results:
        risk = result['actual_risk']
        risk_counts[risk] = risk_counts.get(risk, 0) + 1

    print('Risk Level Distribution:')
    for risk, count in risk_counts.items():
        emoji = '🔥' if risk == 'HIGH' else '⚠️' if risk == 'MEDIUM' else '✅'
        print(f'  {emoji} {risk.upper()}: {count}/{len(TEST_CASES)}')

    passed_percentage = (passed_tests / len(TEST_CASES)) * 100
    print(f'\n✓ Pass rate: {passed_percentage:.1f}% ({passed_tests}/{len(TEST_CASES)})')

    print('\n✓ Test suite completed')


if __name__ == '__main__':
    run_tests()