#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Advanced Xring/Moonsec-style Obfuscation Detector
Detects specific patterns and characteristics of commercial obfuscators
"""

import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Any
from copy import deepcopy


class XringDetector:
    """Detector for Xring and Moonsec-like obfuscation patterns"""

    def __init__(self):
        self.techniques = {
            'proprietaryEncoding': False,
            'runtimeDecryption': False,
            'antiDebug': False,
            'controlFlow': False,
            'stringEncryption': False,
            'functionWrapping': False,
            'bytecodePacker': False,
            'saasProtection': False,
            'antiTamper': False
        }

    def detect(self, code: str):
        """Run comprehensive pattern detection"""
        # Reset detection state
        self.techniques = {k: False for k in self.techniques}

        # Store code for analysis
        self.code = code

        self.analyze_arrays(code)
        self.analyze_decryption(code)
        self.analyze_control_flow(code)
        self.analyze_string_manipulation(code)
        self.analyze_anti_debug(code)
        self.analyze_packing(code)

        return self.techniques

    def analyze_arrays(self, code: str):
        """Look for large hex arrays (common in obfuscators)"""
        hex_array_pattern = re.compile(r'\[\{{{dataset}\}\}%[0-9A-Fa-f]+\]', re.IGNORECASE)
        matches = hex_array_pattern.findall(code)
        if len(matches) > 2:
            self.techniques['stringEncryption'] = True
            self.techniques['proprietaryEncoding'] = True

    def analyze_decryption(self, code: str):
        """Look for decryption patterns"""
        decrypt_patterns = [
            re.compile(r'function\s+(__|||\\[|)\s*decrypt', re.IGNORECASE),
            re.compile(r'local\s+decrypt\s*=\s*function\(', re.IGNORECASE),
            re.compile(r'dofunction\(loadstring', re.IGNORECASE),
            re.compile(r'load\([^()]+\)\(\)', re.IGNORECASE),
        ]

        for pattern in decrypt_patterns:
            if pattern.search(code):
                self.techniques['runtimeDecryption'] = True
                break

    def analyze_control_flow(self, code: str):
        """Look for obfuscated control flow"""
        # Look for excessive nesting
        max_nesting = 0
        current_nesting = 0

        for char in code:
            if char in '{(':
                current_nesting += 1
            elif char in '})':
                current_nesting -= 1

            if current_nesting > max_nesting:
                max_nesting = current_nesting

        if max_nesting > 5:
            self.techniques['controlFlow'] = True

    def analyze_string_manipulation(self, code: str):
        """Look for string processing functions"""
        string_patterns = [
            re.compile(r'%[xX].*'),
            re.compile(r'%[0-9A-Fa-f]+'),
            re.compile(r'%[^xX].*'),
            re.compile(r'_G\[%[0-9A-Fa-f]+\]|\["%[0-9A-Fa-f]+"\]'),
            re.compile(r'string\.split\s*\(', re.IGNORECASE),
            re.compile(r'string\.match\s*\([^)]*%[0-9]', re.IGNORECASE),
            re.compile(r'string\.format%s*\([^)]*%[xcX]', re.IGNORECASE),
        ]

        for pattern in string_patterns:
            if pattern.search(code):
                self.techniques['stringEncryption'] = True
                self.techniques['proprietaryEncoding'] = True
                break

    def analyze_anti_debug(self, code: str):
        """Look for anti-debugging methods"""
        anti_debug_patterns = [
            re.compile(r'(?i)debug\s*\.\s*'),
            re.compile(r'debug\.hook[^;]+'),
            re.compile(r'pause\s*\(', re.IGNORECASE),
            re.compile(r'(pcall|debug\.traceback|debug\.info)(\([^)]*\)|\s+)', re.IGNORECASE),
        ]

        for pattern in anti_debug_patterns:
            match = pattern.search(code)
            if match and not ('//' in match.group(0)):  # Exclude comments
                self.techniques['antiDebug'] = True
                break

    def analyze_packing(self, code: str):
        """Look for packer signatures"""
        packer_signatures = [
            re.compile(r'loadstring\s+suspend', re.IGNORECASE),
            re.compile(r'function\s+hook\s*\(', re.IGNORECASE),
            re.compile(r'eval\s+load\(', re.IGNORECASE),
            re.compile(r'string\.byte\s*-\s*127', re.IGNORECASE),
        ]

        for signature in packer_signatures:
            match = signature.search(code)
            if match and not ('//' in match.group(0)):
                self.techniques['bytecodePacker'] = True
                self.techniques['runtimeDecryption'] = True
                break

    def calculate_severity(self) -> Dict[str, Any]:
        """Calculate overall severity score"""
        active_techniques = [name for name, active in self.techniques.items() if active]

        severity = 0
        likelihoods = {
            'runtimeDecryption': 30,
            'antiDebug': 20,
            'controlFlow': 15,
            'stringEncryption': 15,
            'functionWrapping': 10,
            'bytecodePacker': 15,
            'proprietaryEncoding': 10,
            'saasProtection': 25,
            'antiTamper': 25
        }

        for technique in active_techniques:
            severity += likelihoods.get(technique, 10)

        risk_level = 'LOW'
        if severity > 45:
            risk_level = 'HIGH'
        elif severity > 25:
            risk_level = 'MEDIUM'

        return {
            'level': risk_level,
            'score': min(100, severity),
            'techniques': active_techniques,
            'detected': len(active_techniques) > 0
        }

    def get_recommendations(self, severity: str) -> List[str]:
        """Get analysis recommendations"""
        recommendations = []

        if self.techniques['runtimeDecryption']:
            recommendations.append('⚠️  Runtime decryption detected - scan with sandbox environment')

        if self.techniques['antiDebug']:
            recommendations.append('✓ Anti-debugging mechanisms detected')

        if self.techniques['stringEncryption']:
            recommendations.append('🔍 String encryption patterns found - potential data hiding')

        if self.techniques['controlFlow']:
            recommendations.append('🔄 Complex control flow - use static analysis tools')

        if severity == 'HIGH':
            recommendations.append('🔥 HIGH RISK: This code exhibits characteristics of commercial obfuscators')
            recommendations.append('💡 Isolate this file in a sandbox for analysis')

        elif severity == 'MEDIUM':
            recommendations.append('⚠️  MEDIUM RISK: Consider extensive static analysis')

        return recommendations


class CodeQuotientDifference:
    """Calculate code characteristics metrics"""

    @staticmethod
    def calculate(code: str) -> Dict[str, Any]:
        """Analyze code quotient and density"""
        letters = 0
        numbers = 0
        symbols = 0
        operators = 0
        whitespace = 0

        for char in code:
            if re.search(r'[a-zA-Z]', char):
                letters += 1
            elif re.search(r'[0-9]', char):
                numbers += 1
            elif re.search(r'[{}()\[\];,]', char):
                symbols += 1
            elif re.search(r'[+\-*/=<>!&|^~%]', char):
                operators += 1
            elif re.isspace(char):
                whitespace += 1

        quotient = symbols / (letters + 1) if letters > 0 else 0
        operator_density = operators / (letters + numbers + 1) if (letters + numbers) > 0 else 0

        return {
            'letters': letters,
            'numbers': numbers,
            'symbols': symbols,
            'operators': operators,
            'quotient': quotient,
            'operator_density': operator_density
        }


def advanced_detect(file_path: str) -> Dict[str, Any]:
    """Run advanced detection on a file"""
    try:
        detector = XringDetector()
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        raw_analysis = detector.detect(code)
        risk = detector.calculate_severity()

        return {
            **raw_analysis,
            'file': Path(file_path).name,
            'size': len(code),
            'code_quotient': CodeQuotientDifference.calculate(code),
            'recommendations': detector.get_recommendations(risk['level'])
        }
    except Exception as e:
        print(f'Error analyzing file: {e}')
        return None


def display_advanced_result(result: Dict):
    """Display advanced detection results"""
    print('\n' + '=' * 70)
    print('XRING/MOONSEC-STYLE OBFUSCATION ANALYSIS')
    print('=' * 70)
    print(f"File: {result.get('file', 'Unknown')}")
    print(f"Size: {result.get('size', 0)} bytes")
    print(f"Risk Level: {result.get('level', 'UNKNOWN')}")
    print(f"Obfuscation Score: {result.get('score', 0)}/100")
    print('=' * 70)

    if result.get('detected'):
        print('\n🚨 DETECTED OBFUSCATION TECHNIQUES:')
        for tech in result['techniques']:
            print(f'  ✓ {tech.capitalize()}')

    standard = result.get('code_quotient', {})
    print('\n📊 CODE CHARACTERISTICS:')
    print(f"  - Symbol Density: {(standard.get('quotient', 0) * 100):.1f}%")
    print(f"  - Operator Density: {(standard.get('operator_density', 0) * 100):.1f}%")
    print(f"  - Letters: {standard.get('letters', 0)}")
    print(f"  - Numbers: {standard.get('numbers', 0)}")

    print('\n💡 ANALYSIS RECOMMENDATIONS:')
    for rec in result.get('recommendations', []):
        print(f'  {rec}')

    score = result.get('score', 0)
    if score >= 60:
        print('\n🔥 CRITICAL: This exhibits characteristics of commercial obfuscators')
        print('   Recommended action: isolate in sandbox, analyze with behavioral monitoring')
    elif score >= 35:
        print('\n⚠️  MEDIUM RISK: Consider extensive static analysis')
        print('   recommended action: use security tools, verify with trusted sources')

    print('=' * 70 + '\n')


def simulate_detection(content: str) -> Dict:
    """Simulate detection on content string"""
    detector = XringDetector()
    detector.detect(content)
    return detector.calculate_severity()


def main():
    """Main entry point"""
    args = sys.argv[1:]
    file_path = args[0] if args else None

    if not file_path:
        print('Usage: python advanceddetector.js <file.lua>')
        print('Example: python advanceddetector.js malicious.lua')
        sys.exit(1)

    if not Path(file_path).exists():
        print(f'File not found: {file_path}')
        sys.exit(1)

    result = advanced_detect(file_path)
    if result:
        display_advanced_result(result)

        if '-o' in args:
            output_idx = args.index('-o') + 1 if '-o' in args else len(args) + 1
            output_file = args[output_idx] if output_idx < len(args) else f'{file_path}_analysis.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            print(f'Analysis saved to: {output_file}')


if __name__ == '__main__':
    main()