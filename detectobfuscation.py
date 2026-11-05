#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Lua Code Obfuscation Detection Tool
Produces risk scores and detects common obfuscation patterns
"""

import re
import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple


class ErrorReplacer:
    """Utility for cleaning error messages"""

    REPLACEMENTS = [
        (r'\/data\/data\/com\.termux\/files\/', ''),
        (r'usr\/bin\/lua:\s*', ''),
        (r'\.\/lua\/luacrack\/steps\/', ''),
        (r'\.\/lua\/luacrack\/vmstrings\/', ''),
        (r'[^\\s]+\.lua:\d+:\s*', ''),
        (r'\[C\]:', ''),
        (r'in function', ''),
        (r'stack traceback:', ''),
        (r'^Error:\s*', '', re.IGNORECASE),
    ]

    @staticmethod
    def apply(line: str) -> str:
        result = line
        for pattern, replacement in ErrorReplacer.REPLACEMENTS:
            result = re.sub(pattern, replacement, result)
        return result.strip()


class ObfuscationDetector:
    """Main obfuscation detection class"""

    def __init__(self):
        self.risks: List[Dict] = []
        self.stats = {}

    def add_risk(self, severity: str, category: str, message: str, code_context: str = None):
        """Add a detected risk"""
        self.risks.append({
            'severity': severity,
            'category': category,
            'message': message,
            'code_context': code_context
        })

    def detect_types(self, code: str):
        """Analyze code for obfuscation patterns"""
        stats = {
            'strings': 0,
            'functions': 0,
            'comments': 0,
            'control_flow': 0,
            'string_encoding': set(),
            'self_modifying': False,
            'suspicious_imports': [],
            'variable_name_length': []
        }

        # Remove comments first for detection
        code_without_comments = re.sub(r'--\[=*\[([\s\S]*?)%-=*\]', '', code)

        for line in code_without_comments.split('\n'):
            trimmed = line.strip()

            if not trimmed:
                continue

            # Comment detection
            if trimmed.startswith('--') or re.search(r'--\[=*\[', line):
                stats['comments'] += 1
                continue

            # Function detection
            if re.search(r'\b(function|local function)\s+\w+', line):
                stats['functions'] += 1

            # Variable references
            var_match = re.search(r'local\s+(\w+)\s*=', line)
            if var_match:
                var_name = var_match.group(1)
                if len(var_name) > 0:  # Guard against empty
                    stats['variable_name_length'].append(len(var_name))

            # String detection
            if re.search(r'["\'"]((?:(?!\1)\\.|.)*?)["\']', line):
                stats['strings'] += 1

                # Detect string encoding patterns
                if re.search(r'%[xX][0-9A-Fa-f]+', line):
                    stats['string_encoding'].add('Hex')
                if re.search(r'%[uU][0-9]', line):
                    stats['string_encoding'].add('Unicode')
                if re.search(r'\[[%0-9a-fA-F]+\]', line):
                    stats['string_encoding'].add('ByteArray')

            # Control flow detection
            if re.search(r'\b(if|then|else|elseif|while|for|repeat|until|do|break|return)\s+', line):
                stats['control_flow'] += 1

            # Self-modifying code detection
            if re.search(r'\b(load|string\.byte|string\.char|string\.find|string\.match|string\.gmatch|string\.gsub)\b', line):
                stats['self_modifying'] = True

            # Suspicious imports
            if re.search(r'\b(loadfile|dofile|require|loadstring|getfenv|setfenv)\b', line):
                stats['suspicious_imports'].append(line[:100])

            # String manipulation patterns
            if re.search(r'\bsplit\s*\(', line) or re.search(r'\bconcat\s*\(', line) or re.search(r'\bsub\s*\(', line):
                stats['string_encoding'].add('Manipulation')

            # Base64 detection
            if re.search(r'\bbase64|unpack(%s*,)', line, flags=re.IGNORECASE):
                stats['string_encoding'].add('Base64')

            # Cryptic variable names
            if re.search(r'\b[a-z]{2,3}\s*(?=[(),=\+\-\*/])', line):
                stats['string_encoding'].add('ShortVars')

        self.stats = stats

    def calculate_risk(self) -> Dict:
        """Calculate overall risk level"""
        risk_score = 0

        # Risk factors
        if self.stats['comments'] > 0 and self.stats['functions'] > self.stats['comments'] * 3:
            risk_score += 15
            self.add_risk('medium', 'Code Structure',
                         'High function-to-comment ratio suggests obfuscation')

        if self.stats['self_modifying']:
            risk_score += 20
            self.add_risk('high', 'Self-modifying',
                         'Uses string manipulation functions (self-modifying code detected)')

        if self.stats['suspicious_imports']:
            risk_score += 25
            self.add_risk('high', 'Suspicious Imports',
                         'Uses dangerous runtime functions')

        if len(self.stats['string_encoding']) >= 4:
            risk_score += 15
            self.add_risk('medium', 'String Encoding',
                         'Uses multiple encoding techniques')

        if len({k for k in self.stats.keys() if isinstance(k, str) and k.startswith('global')} or
               set()) > 10:  # Simplified global var check
            risk_score += 10
            self.add_risk('low', 'Code Structure', 'Many global variables')

        # Risk level determination
        if risk_score > 50:
            risk_level = 'HIGH'
        elif risk_score > 25:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'

        return {
            'risk_level': risk_level,
            'obfuscation_score': min(100, risk_score),
            'risks': self.risks,
            'stats': self.stats
        }


class StringPatterns:
    """Registry of common obfuscation patterns"""

    PATTERNS = [
        {
            'name': 'Func Wrapping',
            'severity': 'medium',
            'category': 'Code Structure',
            'score': 10,
            'message': 'Obfuscated function definitions detected',
            'regex': re.compile(r'\beval\s*\(.*?\)', re.IGNORECASE)
        },
        {
            'name': 'Code Injection',
            'severity': 'high',
            'category': 'Security',
            'score': 25,
            'message': 'Uses eval/loadstring - potential code injection risk',
            'regex': re.compile(r'\beval\s*\(.*?\)', re.IGNORECASE)
        },
        {
            'name': 'Byte Generation',
            'severity': 'medium',
            'category': 'Obfuscation',
            'score': 10,
            'message': 'Byte code generation pattern detected',
            'regex': re.compile(r'string\.byte.*string\.char', re.IGNORECASE)
        },
        {
            'name': 'Control Flow',
            'severity': 'low',
            'category': 'Code Structure',
            'score': 5,
            'message': 'Complex control flow detected',
            'regex': re.compile(r'\bif.*then\s+(else|elseif)', re.IGNORECASE)
        },
        {
            'name': 'Reverse Engineering',
            'severity': 'medium',
            'category': 'Obfuscation',
            'score': 15,
            'message': 'Pattern suggests anti-debugging attempts',
            'regex': re.compile(r'\bdebug\s*\.\s*\w+', re.IGNORECASE)
        },
        {
            'name': 'Memory Operations',
            'severity': 'high',
            'category': 'Security',
            'score': 20,
            'message': 'Direct memory operations detected',
            'regex': re.compile(r'string\.sub\s*\([^,]*,\s*-?\d+\)', re.IGNORECASE)
        }
    ]


def analyze_file(file_path: str) -> Tuple[Any, Dict]:
    """Analyze a Lua file for obfuscation"""
    detector = ObfuscationDetector()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        detector.stats['code'] = code
        detector.detect_types(code)
        result = detector.calculate_risk()

        result['file_name'] = Path(file_path).name
        result['file_size'] = len(code)
        result['file_path'] = str(Path(file_path).resolve())

        return result, None
    except Exception as e:
        return None, str(e)


def analyze_string(code: str) -> ObfuscationDetector:
    """Analyze raw Lua code string"""
    detector = ObfuscationDetector()
    detector.stats['code'] = code
    detector.detect_types(code)
    return detector.calculate_risk()


def display_result(result: Dict):
    """Display analysis results"""
    print('\n' + '=' * 60)
    print('OBFUSCATION DETECTION REPORT')
    print('=' * 60)
    print(f"File: {result.get('file_name', 'Unknown')}")
    print(f"Size: {result.get('file_size', 0)} bytes")
    print(f"Risk Level: {result.get('risk_level', 'UNKNOWN')}")
    print(f"Obfuscation Score: {result.get('obfuscation_score', 0)}/100")
    print('=' * 60)

    if result.get('risks'):
        print('\nDETECTED RISKS:')
        for risk in result['risks']:
            print(f'\n[{result["risks"].index(risk) + 1}] {risk["category"]} ({risk["severity"].upper()})')
            print(f'    {risk["message"]}')

    if result.get('stats'):
        stats = result['stats']
        print('\nCODE STATISTICS:')

        string_encodings = ', '.join(stats.get('string_encoding', [])) or 'None'
        print(f"  - Comments: {stats.get('comments', 0)}")
        print(f"  - Functions: {stats.get('functions', 0)}")
        print(f"  - String Encodings: {string_encodings}")
        print(f"  - Self-Modifying: {stats.get('self_modifying', False)}")
        print(f"  - Control Flow Statements: {stats.get('control_flow', 0)}")
        print(f"  - Suspicious Imports: {len(stats.get('suspicious_imports', []))}")

    score = result.get('obfuscation_score', 0)
    if score >= 50:
        print('\n⚠️  HIGH RISK: This code appears heavily obfuscated!')
    elif score >= 25:
        print('\n⚠️  MEDIUM RISK: Some obfuscation patterns detected')
    print('=' * 60 + '\n')


def main():
    """Main entry point"""
    args = sys.argv[1:]

    if len(args) == 0:
        print('Usage: python detectobfuscation.py <file.lua> [options]')
        print('Options:')
        print('  -v, --verbose      Enable verbose output')
        print('  -i, --interactive  Interactive mode')
        print('  -o, --output <file>  Save results to JSON file')
        sys.exit(1)

    first_arg = args[0]
    is_path = Path(first_arg).exists() and first_arg.endswith('.lua')

    if is_path:
        result, error = analyze_file(first_arg)
        if result:
            display_result(result)

            if '-o' in args or '--output' in args:
                output_idx = args.index('-o')
                if output_idx + 1 < len(args):
                    output_file = args[output_idx + 1]
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2)
                    print(f'Results saved to {output_file}')
        else:
            print(f'Error: {error}')
            sys.exit(1)
    else:
        # String analysis mode
        code = first_arg
        if '-i' in args or '--interactive' in args:
            print('Enter Lua code to analyze (Ctrl+D or Ctrl+Z to finish):')
            try:
                input_code = []
                for chunk in sys.stdin:
                    input_code.append(chunk)
                code = ''.join(input_code)
            except KeyboardInterrupt:
                code = ''
            except EOFError:
                code = ''

            if not code:
                print('No input code provided')
                sys.exit(1)

            result = analyze_string(code)
            display_result(result)
        else:
            result = analyze_string(code)
            display_result(result)


if __name__ == '__main__':
    main()