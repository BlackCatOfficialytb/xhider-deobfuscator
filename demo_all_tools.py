#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive demonstration of the obfuscation detection suite
Shows integration between all detection tools
"""

import sys
import json
import re
from pathlib import Path

from detector_utils import ObfuscationScanner, generate_summary


# Sample code profiles from detector_utils.py using Strings literals with double quotes ok
SAMPLES = {
    'clean': {
        'name': 'Clean Lua Code',
        'code': '''-- Example clean Lua script
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
'''
    },
    'simpleObf': {
        'name': 'Simple Obfuscation',
        'code': '''-- Custom variable names only
local _a = 10
local _b = 20
local _c = _a + _b

-- Conditional logic
if _c > 25 then
  print("Greater")
else
  print("Less")
end
'''
    },
    'xring': {
        'name': 'Xring-style Obfuscation',
        'code': '''-- Xring-style patterns
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
'''
    },
    'commercial': {
        'name': 'Commercial Packer',
        'code': '''-- Heavy commercial packer patterns
__G = loadstring or error
_G.deobfuscate = function()
  -- Deeply nested structures
  local function ____(module)
    local _ = {}

    _.__ = function()
      local result = eval(function()
        -- Custom encoding
        local charSets = {
          "   ",
          "__  ",
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
'''
    }
}


def helper_generate_bot_response(risk_level, score, techniques):
    """Helper to format bot response"""
    RISK_EMOJIS = {'HIGH': '🚨', 'MEDIUM': '⚠️', 'LOW': '✅'}

    emoji = RISK_EMOJIS.get(risk_level, '❓')
    techniques_count = len(techniques) if techniques else 0

    response = f"**{emoji} DEObfuscation Analysis Result**\n\n"
    response += f"**Risk Level:** {risk_level.upper()}\n"
    response += f"**Score:** {score}/100\n"
    response += f"**Detected Techniques:** {techniques_count}\n\n"

    if risk_level == 'HIGH':
        response += '**🚨 SECURITY ACTION REQUIRED**\n\n'
        response += 'This script exhibits multiple obfuscation patterns commonly used in\n'
        response += 'malicious code. It is recommended to:\n\n'
        response += '• BLOCK immediate execution\n'
        response += '• Isolate in sandbox environment\n'
        response += '• Require administrator approval'
    elif risk_level == 'MEDIUM':
        response += '**⚠️ REVIEW REQUIRED**\n\n'
        response += 'This script shows some suspicious patterns. Before execution:\n\n'
        response += '• Manually inspect the code\n'
        response += '• Verify source reputation\n'
        response += '• Consider additional analysis'
    else:
        response += '**✅ SAFE PROCESSING**\n\n'
        response += 'This script appears clean. Proceed with caution as always.\n'
        response += 'Consider additional testing if the code is from an unknown source.'

    return response


def demo_parallel_analysis():
    """Demo 1: Parallel analysis of all samples"""
    print('📊 RUN 1: Parallel Analysis of All Samples\n')
    print('═' * 70)

    scanner = ObfuscationScanner()
    results = []

    for key, sample in SAMPLES.items():
        detection_result = scanner.scan(sample['code'], log=False)
        summary = generate_summary(detection_result)

        # Extract risk level from summary
        risk_match = re.search(r'Detection Result: (\w+)', summary)
        risk_level = risk_match.group(1) if risk_match else 'LOW'

        result = {
            'name': sample['name'],
            'key': key,
            'summary': summary,
            'riskLevel': risk_level,
            'techniques': detection_result.get('techniques', [])
        }

        results.append(result)

    return results


def demo_risk_workflow(sample):
    """Demo 2: Risk assessment workflow"""
    print('\n🎯 RUN 2: Risk Assessment Workflow\n')
    scanner = ObfuscationScanner()
    result = scanner.scan(sample['code'], log=True)
    summary = generate_summary(result)

    print(summary)

    # Decision tree
    print('\n📋 DECISION TRAJECTORY:')
    if result['riskLevel'] == 'HIGH':
        print('  🔥 ACTION: BLOCK IMMEDIATELY')
        print('  🎯 REASON: Multiple risk factors detected')
        print('  🔍 RECOMMENDATION: Isolate in sandbox for behavioral analysis')
    elif result['riskLevel'] == 'MEDIUM':
        print('  ⚠️  ACTION: REQUIRES MANUAL REVIEW')
        print('  🎯 REASON: Suspicious patterns but not clearly malicious')
        print('  🔍 RECOMMENDATION: Inspect source code manually')
    else:
        print('  ✅ ACTION: APPROVE WITH MONITORING')
        print('  🎯 REASON: Code appears clean')
        print('  🔍 RECOMMENDATION: Continue with normal processing')

    return result


def demo_technical_analysis(sample):
    """Demo 3: Technical detail analysis"""
    print('\n🔬 RUN 3: Technical Detail Analysis\n')
    scanner = ObfuscationScanner()
    result = scanner.scan(sample['code'], log=False)

    print('DETECTED CHARACTERISTICS:\n')

    if result['techniques'] and len(result['techniques']) > 0:
        print('Obfuscation Techniques:')
        for i, tech in enumerate(result['techniques'], 1):
            emoji = '🔧' if 'Runtime' in tech else '🛡️' if 'Anti' in tech else '📦'
            print(f'  {emoji} {i}. {tech}')
    else:
        print('  ✅ No obfuscation techniques detected')

    print('\nRECOMMENDATIONS:')
    if result.get('recommendations') and len(result['recommendations']) > 0:
        for i, rec in enumerate(result['recommendations'], 1):
            print(f'  {i}. {rec}')
    else:
        print('  None required')


def demo_bot_integration():
    """Demo 4: Discord bot integration example"""
    print('\n🔥 RUN 4: Discord Bot Integration Example\n')
    fake_user_script = SAMPLES['xring']['code']

    # Simulate bot processing
    print('simulating Discord bot receiving user script...\n')

    scanner = ObfuscationScanner()
    result = scanner.scan(fake_user_script, log=True)

    # Bot response logic
    bot_response = helper_generate_bot_response(
        result['riskLevel'],
        result['score'],
        result.get('techniques', [])
    )
    print(bot_response)

    return result


def generate_audit_summary(results):
    """Generate a summary and stats for multiple results"""
    total = len(results)
    blocked = sum(1 for r in results if r['riskLevel'] == 'HIGH')
    medium = sum(1 for r in results if r['riskLevel'] == 'MEDIUM')
    passed = total - blocked - medium

    print(f'\n╔══{'═' * 68}╗')
    print(f'║{"📊  ALL TESTS COMPLETE - AUDIT SUMMARY":^76}║')
    print(f'╠{'═' * 68}╣')

    print(f'\nTotal Files Scanned: {total}')
    print(f'Blocked: {blocked} ({(blocked/total*100):.1f}%)')
    print(f'Medium Risk: {medium} ({(medium/total*100):.1f}%)')
    print(f'Passed: {passed} ({(passed/total*100):.1f}%)')

    risk_counts = {}
    for r in results:
        risk = r['riskLevel']
        risk_counts[risk] = risk_counts.get(risk, 0) + 1

    print('\nRisk Level Distribution:')
    for risk, count in risk_counts.items():
        emoji = '🔥' if risk == 'HIGH' else '⚠️' if risk == 'MEDIUM' else '✅'
        print(f'  {emoji} {risk.upper()}: {count}/{total}')


def run_all_demos():
    """Run all demonstrations"""
    try:
        # Demo 1: Parallel analysis
        results = demo_parallel_analysis()

        print('\n' + '═' * 70)
        print('📊 PARALLEL ANALYSIS COMPLETED')
        print('═' * 70)

        for result in results:
            status = '🔥' if result['riskLevel'] == 'HIGH' else '⚠️' if result['riskLevel'] == 'MEDIUM' else '✅'
            score_match = result['summary'].find('/100')
            if score_match > 0:
                print(f'\n{status} {result["name"]}: {result["riskLevel"].upper()} (Score: {result["summary"][score_match - 4:score_match]})')
            else:
                print(f'\n{status} {result["name"]}: {result["riskLevel"].upper()}')

        # Demo 2: Risk workflow
        demo_risk_workflow(SAMPLES['simpleObf'])

        # Demo 3: Technical analysis
        demo_technical_analysis(SAMPLES['commercial'])

        # Demo 4: Bot integration
        demo_bot_integration()

        # Summary
        generate_audit_summary(results)

        print('\n' + '═' * 70)
        print('📚 DEMONSTRATION COMPLETE')
        print('═' * 70)
        print('\nKey Takeaways:\n')
        print('1. Multiple detection tools provide comprehensive coverage')
        print('2. Risk assessment should use decision trees not automatic blocking')
        print('3. Integration with bots requires careful response generation')
        print('4. Always consider context and user reputation')

    except Exception as error:
        print(f'\nDemo Error: {error}')
        return False

    return True


if __name__ == '__main__':
    success = run_all_demos()
    if success:
        print('\n✨ All demonstrations completed successfully!\n')
        sys.exit(0)
    else:
        print('\n❌ Demonstration failed\n')
        sys.exit(1)