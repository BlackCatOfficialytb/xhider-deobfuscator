# Lua Code Obfuscation Detection Tools

This repository contains security-focused detection tools for identifying obfuscated Lua code, including patterns similar to Xring and Moonsec obfuscators.

## 🛡️ Overview

The detection suite includes three tools:

1. **Basic Detector** (`detectobfuscation.js`) - General obfuscation detection
2. **Advanced Detector** (`advanceddetector.js`) - Xring/Moonsec-style patterns
3. **Utility Module** (`detector-utils.js`) - Integration-friendly module for bots

## 📊 Detection Capabilities

### Common Obfuscation Patterns Detected

- **Runtime Decryption** - Detects eval/loadstring patterns
- **String Encryption** - Finds string manipulation and encoding
- **Anti-Debugging** - Identifies debug hook mechanisms
- **Proprietary/Packed Code** - Recognizes packer signatures
- **Control Flow Obfuscation** - High nesting/complexity detection
- **Suspicious Imports** - Dark patterns and dangerous functions

### Risk Levels

- 🔥 **HIGH** (50-100) - Heavily obfuscated or packed code
- ⚠️ **MEDIUM** (25-49) - Some obfuscation patterns present
- ✅ **LOW** (0-24) - Clean code, minimal concerns

## 🚀 Usage

### Basic Detection

```bash
# Scan a single file
node detectobfuscation.js malicious.lua

# Interactive mode
node detectobfuscation.js -i

# Save results to JSON
node detectobfuscation.js script.lua -o output.json
```

### Advanced Detection

```bash
# Scan for Xring/Moonsec patterns
node advanceddetector.js suspicious.lua

# Save detailed analysis
node advanceddetector.js script.lua -o detailed.json
```

### Batch Scanning

```bash
# Scan a directory
node detector-utils.js -m ./scripts

# Scan single file
node detector-utils.js script.lua

# Verbose mode
node detector-utils.js script.lua -v
```

## 🔍 Integration with Discord Bot

The `detector-utils.js` module can be integrated into your existing Discord bot:

```javascript
const { ObfuscationScanner, generateSummary } = require('./detector-utils');

app.post('/scan', async (req, res) => {
  const code = req.body.code;
  const scanner = new ObfuscationScanner();
  const result = scanner.scan(code);

  return res.json({
    riskLevel: result.riskLevel,
    score: result.score,
    techniques: result.techniques,
    recommendations: result.recommendations
  });
});
```

### Bot Integration Example

```javascript
// In your Discord bot
async function checkObfuscation(code) {
  const scanConst = new ObfuscationScanner();
  const result = scanConst.scan(code, { log: false });

  if (result.riskLevel === 'HIGH') {
    await message.reply('🚨 This script appears heavily obfuscated. Use caution!');
    return true;
  }
  return false;
}
```

## 📝 Output Format

### Basic Detector Output

```
============================================================
OBFUSCATION DETECTION REPORT
============================================================
File: malicious.lua
Size: 15234 bytes
Risk Level: HIGH
Obfuscation Score: 78/100
============================================================

DETECTED RISKS:
[1] Anti-debugging (HIGH)
    Uses string manipulation functions...

CODE STATISTICS:
  - Comments: 45
  - Functions: 156
  - String Encodings: Hex, Unicode, ByteArray
  - Self-Modifying: true
  - Control Flow Statements: 87
  - Suspicious Imports: 12
============================================================
```

### Advanced Detector Output

```
======================================================================
XRING/MOONSEC-STYLE OBFUSCATION ANALYsis
======================================================================
File: xring.lua
Size: 23412 bytes
Risk Level: HIGH
Obfuscation Score: 92/100
======================================================================

🚨 DETECTED OBFUSCATION TECHNIQUES:
  ✓ runtimeDecryption
  ✓ proprietaryEncoding
  ✓ antiDebug
  ✓ stringEncryption
  ✓ controlFlow

📊 CODE CHARACTERISTICS:
  - Symbol Density: 35.2%
  - Operator Density: 18.7%
  - Letters: 12450
  - Numbers: 3456

💡 ANALYSIS RECOMMENDATIONS:
  ⚠️  Runtime decryption detected - scan with sandbox environment
  ✓ Anti-debugging mechanisms detected
  🔍 String encryption patterns found - potential data hiding
  🔄 Complex control flow - use static analysis tools
  🔥 HIGH RISK: This code appears heavily obfuscated or packed
  💡 Isolate this file in a sandbox for analysis
======================================================================
```

## 🎯 Use Cases

### Security Monitoring
- Detect malicious scripts automatically
- Flag suspicious code before execution
- Real-time validation of user-submitted code

### Malware Analysis
- Identify obfuscation techniques
- Guide forensic analysis
- Create signatures for known patterns

### Code Auditing
- Review open-source contributions
- Validate script safety
- Ensure compliance requirements

## ⚠️ Limitations

1. **Static Analysis Only** - These tools do not execute code
2. **False Positives** - Some legitimate code may trigger patterns
3. **Obfuscation Evasion** - Advanced packers can bypass basic detection
4. **No Behavior Monitoring** - Only detects patterns, not runtime behavior

## 🔬 Best Practices

1. **Always Verify** - Use multiple detection tools for important files
2. **Sandbox Testing** - Execute high-risk code in isolated environments
3. **Whitelist Known Good** - Create known-safe signatures
4. **Update Patterns** - Regularly update detection signatures
5. **Document Findings** - Record analysis results for future reference

## 🧪 Testing

Test the detection suite with sample obfuscated code:

```javascript
const scanner = require('./detector-utils');
const fs = require('fs');

const code = fs.readFileSync('test.lua', 'utf-8');
const result = scanner.scan(code);

console.log(JSON.stringify(result, null, 2));
```

## 📚 References

- Lua Obfuscation Techniques (various security research papers)
- Xring Analysis Reports
- Moonsec Analysis Documentation
- Lua Security Best Practices

## 🤝 Contributing

To improve detection accuracy:

1. Analyze new obfuscation samples
2. Update pattern matching rules
3. Add new detection methods
4. Contribute improvements to the repository

## 📄 License

These tools are provided for educational and security purposes only. Use responsibly and ethically.

---
**Note**: These tools are for detection purposes only. They do not provide deobfuscation capabilities.