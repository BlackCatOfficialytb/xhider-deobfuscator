#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module for obfuscation detection integration
Can be used for security monitoring and bot integration
"""

import re
import sys
from pathlib import Path
from typing import List, Set, Dict, Any, Optional


class ObfuscationScanner:
    """
    Simple static analysis for obfuscation detection
    Can be imported and used within bot/environment
    """

    def __init__(self):
        self.techniques = {
            'proprietaryEncoding': False,
            'runtimeDecryption': False,
            'antiDebug': False,
            'stringEncryption': False,
            'controlFlow': False,
            'suspiciousImports': False
        }

    def scan(self, code: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Scan Lua code for obfuscation patterns

        Args:
            code: Lua code to analyze
            options: Dictionary with keys like 'log' (bool)

        Returns:
            Dictionary with detection results
        """
        options = options or {}
        log = options.get('log', False)

        # Reset detection state
        for key in self.techniques:
            self.techniques[key] = False

        # Store code for analysis
        self.code = code

        # Implement pattern detection methods
        self._detect_packing()
        self._detect_runtime_decryption()
        self._detect_string_encryption()
        self._detect_anti_debug()
        self._detect_control_flow()
        self._detect_suspicious_imports()

        risk = self._calculate_risk()

        if log and risk['level'] == 'HIGH':
            print(f'[SCANNER] Obfuscated script detected: {risk["score"]}%')

        return {
            'riskLevel': risk['level'],
            'score': risk['score'],
            'techniques': [name for name, active in self.techniques.items() if active],
            'recommendations': self._get_recommendations(risk['level'])
        }

    def _detect_packing(self):
        """Detect proprietary/packed code"""
        packer_signatures = [
            r'\bloadstring\s+suspend',
            r'dofunction\(loadstring',
            r'function\s+hook\s*\(',
        ]

        for pattern in packer_signatures:
            if re.search(pattern, self.code, re.IGNORECASE) and not re.search('//', self.code):
                self.techniques['proprietaryEncoding'] = True
                self.techniques['runtimeDecryption'] = True
                break

    def _detect_runtime_decryption(self):
        """Detect runtime decryption patterns"""
        patterns = [
            r'function\s+(__|d|_|\[)decrypt',
            r'loadstring\(.*?\)',
            r'dofunction\(loadstring',
            r'local\s+decrypt\s*=\s*function\(',
        ]

        for pattern in patterns:
            if re.search(pattern, self.code, re.IGNORECASE) and not re.search('//', self.code):
                self.techniques['runtimeDecryption'] = True
                break

    def _detect_string_encryption(self):
        """Detect string encryption patterns"""
        has_hex_escapes = bool(re.search(r'%[xX]', self.code))
        has_hex_codes = bool(re.search(r'%[0-9A-Fa-f]+', self.code))
        has_multi_char = bool(re.search(r'%[^xX]', self.code))

        # Check for byte manipulation patterns
        if has_hex_escapes and (has_hex_codes or has_multi_char):
            self.techniques['stringEncryption'] = True

        # Check for custom byte array patterns
        if '%[' in self.code or '%]' in self.code:
            self.techniques['stringEncryption'] = True

    def _detect_anti_debug(self):
        """Detect anti-debugging methods"""
        patterns = [
            r'debug\s*\.',
            r'debug\.hook',
            r'pcall.*debug',
        ]

        for pattern in patterns:
            if re.search(pattern, self.code, re.IGNORECASE) and not re.search('//', self.code):
                self.techniques['antiDebug'] = True
                break

    def _detect_control_flow(self):
        """Detect complex control flow"""
        # Look for excessive nesting
        max_nesting = 0
        current_nesting = 0

        for line in self.code.split('\n'):
            trimmed = line.strip()
            if trimmed.startswith('f') or trimmed.startswith('l'):
                current_nesting += 1
            elif trimmed.startswith('elseif') or trimmed.startswith('else'):
                current_nesting -= 1

            if current_nesting > max_nesting:
                max_nesting = current_nesting

        if max_nesting > 4:
            self.techniques['controlFlow'] = True

    def _detect_suspicious_imports(self):
        """Detect suspicious imports"""
        patterns = [
            r'require',
            r'require\s*\(',
        ]

        for pattern in patterns:
            if re.search(pattern, self.code, re.IGNORECASE) and not re.search('//', self.code):
                self.techniques['suspiciousImports'] = True
                break

    def _calculate_risk(self) -> Dict[str, Any]:
        """Calculate overall risk level"""
        score = 0

        if self.techniques['runtimeDecryption']:
            score += 30
        if self.techniques['proprietaryEncoding']:
            score += 20
        if self.techniques['antiDebug']:
            score += 20
        if self.techniques['stringEncryption']:
            score += 15
        if self.techniques['controlFlow']:
            score += 15
        if self.techniques['suspiciousImports']:
            score += 10

        risk_level = 'LOW'
        if score > 50:
            risk_level = 'HIGH'
        elif score > 25:
            risk_level = 'MEDIUM'

        return {'level': risk_level, 'score': score}

    def _get_recommendations(self, level: str) -> List[str]:
        """Get recommendations based on risk level"""
        recommendations = []

        if self.techniques['runtimeDecryption']:
            recommendations.append('Runtime decryption detected - requires sandboxed analysis')

        if self.techniques['antiDebug']:
            recommendations.append('Anti-debugging mechanisms present')

        if self.techniques['proprietaryEncoding']:
            recommendations.append('Proprietary/packed encoding detected')

        if level == 'HIGH':
            recommendations.append('HIGH RISK: Consider isolating this script in a sandbox environment')

        if level == 'MEDIUM':
            recommendations.append('MEDIUM RISK: Extended analysis recommended')

        return recommendations


def scan_multiple_files(file_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Batch scan multiple files

    Args:
        file_paths: List of file paths to scan

    Returns:
        List of scan results
    """
    results = []

    for file_path in file_paths:
        try:
            path = Path(file_path)
            if path.is_dir():
                files = [f for f in path.iterdir() if f.suffix == '.lua']
                for file in files:
                    code = file.read_text(encoding='utf-8')
                    scanner = ObfuscationScanner()
                    result = scanner.scan(code, log=False)
                    results.append({
                        'file': file.name,
                        'path': str(file),
                        **result
                    })
            else:
                code = path.read_text(encoding='utf-8')
                scanner = ObfuscationScanner()
                result = scanner.scan(code)
                results.append({
                    'file': path.name,
                    'path': str(path),
                    **result
                })
        except Exception as error:
            print(f'Error scanning {file_path}: {error}')

    return results


def generate_summary(scan_result: Dict) -> str:
    """
    Generate human-friendly detection summary

    Args:
        scan_result: Scan result from scanner

    Returns:
        Human-readable summary string
    """
    risk_level = scan_result.get('riskLevel', 'UNKNOWN')
    emoji = '🔥' if risk_level == 'HIGH' else '⚠️' if risk_level == 'MEDIUM' else '✅'

    summary = f"{emoji} Detection Result: {risk_level.upper()}\n"
    summary += f"  📊 Score: {scan_result.get('score', 0)}/100\n"
    summary += f"  🎯 Techniques detected: {'Yes' if scan_result.get('techniques') and len(scan_result['techniques']) > 0 else 'None'}\n"

    return summary


# For command-line usage
if __name__ == '__main__':
    if len(sys.argv) < 2 or '-h' in sys.argv or '--help' in sys.argv:
        print('Lua Obfuscation Scanner')
        print('\nUsage: python detector_utils.py [options] <file.lua>')
        print('\nOptions:')
        print('  -o, --output <file>   Save results to file')
        print('  -v, --verbose         Verbose output')
        print('  -m, --multiple <dir>  Scan all .lua files in directory')
        print('  -j, --json            Output as JSON')
        print('\nExample:')
        print('  python detector_utils.py script.lua')
        print('  python detector_utils.py -m ./scripts')
        sys.exit(0)

    def process_single_file(file_path: str):
        if not Path(file_path).exists():
            print(f'File not found: {file_path}')
            return

        print(f'\n🔍 Scanning: {file_path}')
        code = Path(file_path).read_text(encoding='utf-8')
        scanner = ObfuscationScanner()
        result = scanner.scan(code)

        print(generate_summary(result))

        if result['riskLevel'] == 'HIGH' and '-v' in sys.argv or '--verbose' in sys.argv:
            print(f'\n  🎯 Detected Techniques ({len(result["techniques"])}):')
            for tech in result['techniques']:
                print(f'     • {tech}')
            if result.get('recommendations'):
                print('\n  💡 Recommendations:')
                for rec in result['recommendations']:
                    print(f'     {rec}')

    def process_directory(dir_path: str):
        directory = Path(dir_path)
        if not directory.exists():
            print(f'Directory not found: {dir_path}')
            return

        # If multiple option, get the actual directory path
        idx = sys.argv.index('-m')
        if idx + 1 < len(sys.argv):
            target = sys.argv[idx + 1]
            directory = Path(target)

        scanner = ObfuscationScanner()
        results = scan_multiple_files([str(directory)])

        print('\n' + '=' * 70)
        print('BATCH SCAN RESULTS')
        print('=' * 70 + '\n')

        total = len(results)
        blocked = 0
        flagged = 0
        passed = 0

        for result in results:
            print(generate_summary(result))
            if result['riskLevel'] == 'HIGH':
                blocked += 1
                print(f'  🔥 {result["file"]}')
            elif result['riskLevel'] == 'MEDIUM':
                flagged += 1
            else:
                passed += 1

        print(f'\n{'=' * 70}')
        print(f'Total files scanned: {total}')
        print(f'Blocked: {blocked} ({(blocked/total*100):.1f}%)')
        print(f'Flagged: {flagged} ({(flagged/total*100):.1f}%)')
        print(f'Passed:  {passed} ({(passed/total*100):.1f}%)')

    # Handle command line arguments
    if '-m' in sys.argv:
        idx = sys.argv.index('-m')
        if idx + 1 < len(sys.argv):
            process_directory(sys.argv[idx + 1])
    else:
        process_single_file(sys.argv[1])