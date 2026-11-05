# 🛡️ Obfuscation Detection Suite

A complete set of security tools for detecting Lua code obfuscation patterns, including Xring and Moonsec-like techniques.

## 📁 Files Included

| Tool | Description | Usage |
|------|-------------|-------|
| `detectobfuscation.js` | Basic pattern detection | `node detectobfuscation.js <file.lua>` |
| `advanceddetector.js` | Xring/Moonsec analysis | `node advanceddetector.js <file.lua>` |
| `detector-utils.js` | Bot integration module | Import and use in your bot |
| `test-tool.js` | Test suite | `node test-tool.js` |
| `sample-obfuscated.lua` | Test sample | For testing detection tools |

## 🎯 Quick Start

### 1. Basic Detection

Scans for common obfuscation patterns:
```bash
node detectobfuscation.js sample-obfuscated.lua
```

Output:
```
============================================================
OBFUSCATION DETECTION REPORT
============================================================
File: sample-obfuscated.lua
Size: 1623 bytes
Risk Level: HIGH
Obfuscation Score: 55/100
============================================================

DETECTED RISKS:
[1] Self-modifying (HIGH)
    Uses string manipulation functions...

[2] Suspicious Imports (HIGH)
    Uses dangerous runtime functions

⚠️  HIGH RISK: This code appears heavily obfuscated!
============================================================
```

### 2. Advanced Xring Detection

Scans for advanced obfuscation characteristics:
```bash
node advanceddetector.js sample-obfuscated.lua
```

Output:
```
======================================================================
XRING/MOONSEC-STYLE OBFUSCATION ANALYSIS
======================================================================
File: Xring.lua
Risk Level: HIGH
Obfuscation Score: 92/100
============================================================

🚨 DETECTED OBFUSCATION TECHNIQUES:
  ✓ runtimeDecryption
  ✓ antiDebug
  ✓ stringEncryption
  ✓ controlFlow

💡 ANALYSIS RECOMMENDATIONS:
  ⚠️  Runtime decryption detected - scan with sandbox environment
  ✓ Anti-debugging mechanisms detected
  🔍 String encryption patterns found
  🔥 HIGH RISK: This code appears heavily obfuscated
======================================================================
```

### 3. Test the Tools

Run the test suite to verify everything works:
```bash
node test-tool.js
```

Output:
```
🧪 Running Obfuscation Detection Tests
===============================================

📝 Test Case: Clean Lua Script
----------------------------------------------------------------------

✅ Detection Result: LOW
  📊 Score: 0/100

📝 Test Case: Xring-style Patterns
----------------------------------------------------------------------

🔥 Detection Result: HIGH
  📊 Score: 65/100
  🎯 Detected Techniques (3):
     • runtimeDecryption
     • antiDebug
     • controlFlow

✓ All tests completed successfully!
```

## 🔌 Integration with Discord Bot

### Method 1: Direct Integration

```javascript
// In your main bot file
const { ObfuscationScanner } = require('./detector-utils');

// Add this function to process user submissions
async function checkObfuscation(code, botMessage) {
  const scanner = new ObfuscationScanner();

  // Scan the submitted code
  const result = scanner.scan(code, { log: true });

  // Return early if highly obfuscated
  if (result.riskLevel === 'HIGH') {
    await botMessage.reply(
      '🚨 **SECURITY ALERT**: This script exhibits obfuscation patterns typically found in\n' +
      '  malicious code. Only proceed if you understand the code purpose.\n\n' +
      `  Risk Score: ${result.score}/100\n\n` +
      `  Detected: ${result.techniques.length} techniques\n` +
      `  ${result.recommendations[0] || ''}`
    );
    return true; // Blocked
  }

  if (result.riskLevel === 'MEDIUM') {
    await botMessage.reply(
      '⚠️ **PRECAUTION**: This script shows some obfuscation patterns. Review carefully.',
      { allowedMention: { parse: ['users'] } }
    );
    return false; // Allow, but notify
  }

  // Low risk or clean script - proceed
  await botMessage.reply('✅ Code approved for analysis');
  return false; // Allow
}
```

### Method 2: Command Integration

```javascript
// Add to your bot command handling
if (command === '!check' || command === '!scan') {
  const scanner = new ObfuscationScanner();
  const result = scanner.scan(message.content, { log: false });

  let response = '';
  if (result.riskLevel === 'HIGH') {
    response = `🚨 HIGH RISK (${result.score}/100)\n` +
               `Detected: ${result.techniques.join(', ')}\n\n` +
               result.recommendations.join('\n');
  } else if (result.riskLevel === 'MEDIUM') {
    response = `⚠️ MEDIUM RISK (${result.score}/100)\n` +
               `Detected: ${result.techniques.join(', ')}`;
  } else {
    response = `✅ LOW RISK (${result.score}/100)\n` +
               `Code appears clean and readable.`;
  }

  await message.reply(response);
}
```

## 📊 Detection Capabilities

### What Gets Detected

- **Runtime Decryption** - eval/loadstring patterns
- **Anti-Debugging** - debug.gethook, pause() functions
- **String Encryption** - custom escape sequences, alphases
- **Control Flow Obfuscation** - excessive nesting, complex conditionals
- **Proprietary Encoding** - proprietary packer signatures
- **Suspicious Imports** - dangerous file loading functions

### Risk Levels Explained

| Risk Level | Score Range | Detection | Action |
|------------|-------------|-----------|--------|
| 🔥 **HIGH** | 50-100 | Multiple techniques | BLOCK - Requires sandbox analysis |
| ⚠️ **MEDIUM** | 25-49 | 1-2 techniques | REVIEW - Manual inspection required |
| ✅ **LOW** | 0-24 | Clean or minimal | ALLOW - Proceed with caution |

## 🎓 Best Practices

### Security Workflow

1. **Detection Phase** - Run detection tools on all incoming submissions
2. **Assessment** - Review detected techniques to understand risks
3. **Isolation** - Execute high-risk code in sandbox environment
4. **Logging** - Record all scans and detection results
5. **Whitelisting** - Create known-good code signatures

### Integration Tips

```javascript
// Recommendations for production use
const detectorConfig = {
  onHighRisk: (file, result) => {
    // Log high-risk files
    console.log(`[SECURITY] BLOCKED: ${file}`);
    console.log(`  Score: ${result.score}`);
    console.log(`  Techniques: ${result.techniques.join(', ')}`);
  },

  onMediumRisk: (file, result) => {
    // Notify administrators
    console.log(`[WARNING] MODERATED: ${file}`);
  }
};
```

## 🔬 Detailed Pattern Examples

### Xring-style Patterns Detected

```lua
-- Custom decoding function
local function decodeString(encoded)
  local result = ""
  for i = 1, #encoded do
    local char = encoded:sub(i, i)
    if char == '%' then
      local charCode = tonumber(encoded:sub(i+1, i+2), 16)
      result = result .. string.char(charCode)
    end
  end
  return result
end

-- Anti-debugging check
local isDebuggerAttached = false
if debug.getenv then
  isDebuggerAttached = true
end

if isDebuggerAttached then
  return nil  -- Block debugger
end

-- Runtime code execution
loadstring(decrypted)()
```

### Moonsec-style Patterns Detected

```lua
-- Character array manipulation
local charset = "%[]{}"  -- ... padding for security

-- Complex function structure
local function ____(__, ____)
  -- ... highly obfuscated body
end

-- String processing
local string = gsub(string, "([%w%~%+]+)", ...)
```

## 🔧 Configuration Options

### Environment Variables

```bash
# Set detection thresholds
export DETECTION_threshold=50  # Risk score cutoff for blocking

# Enable verbose logging
export DETECTION_verbose=true

# Add custom patterns
export DETECTION_patterns=/path/to/custom_patterns.json
```

### Custom Pattern Files

Create `patterns.json`:
```json
{
  "customPatterns": [
    {
      "name": "MyCustomObfuscation",
      "score": 20,
      "regex": "/my_custom_pattern/gi"
    }
  ]
}
```

## 📈 Reporting and Analytics

### Scan Statistics

Monitor detection trends:
```javascript
const statistics = {
  totalScans: 1247,
  blockedScans: 156,
  flaggedScans: 432,
  cleanScans: 660,
  avgRiskScore: 37.2,
  detectionRate: 74.3
};

console.log('Detection Statistics:');
console.log(`  Total: ${statistics.totalScans}`);
console.log(`  Blocked: ${statistics.blockedScans} (${(statistics.blockedScans/statistics.totalScans*100).toFixed(1)}%)`);
```

### Generate Reports

```javascript
const { ObfuscationScanner } = require('./detector-utils');

async function generateReport(filePath) {
  const scanner = new ObfuscationScanner();
  const code = fs.readFileSync(filePath, 'utf-8');
  const result = scanner.scan(code);

  const report = {
    fileName: path.basename(filePath),
    riskLevel: result.riskLevel,
    score: result.score,
    techniques: result.techniques,
    recommendations: result.recommendations,
    scanDate: new Date().toISOString()
  };

  return report;
}
```

## 🚨 Important Notes

### Detection Limitations

- **Static Analysis Only** - Tools do not execute code
- **False Positives** - Legitimate code may trigger patterns
- **Evasion Techniques** - Advanced obfuscators can bypass detection
- **Runtime Behavior** - Pattern matching doesn't capture dynamic behavior

### When to Use

### Use When:
- ✅ Reviewing user-submitted code for security
- ✅ Analyzing open-source contributions
- ✅ Auditing third-party scripts
- ✅ Pre-execution validation
- ✅ Educational purposes

### Don't Use When:
- ❌ Primary malware analysis (use sandbox execution)
- ❌ Legal proceedings (use specialized tools)
- ❌ Production enforcement (use multiple layers of defense)
- ❌ Absolute security guarantee (no tool guarantees 100% detection)

## 🤝 Contributing

To improve detection accuracy:

1. Analyze new obfuscated samples
2. Update pattern matching rules
3. Add detection for new obfuscation techniques
4. Submit improvements through pull requests
5. Update documentation

## 📚 References

- [Lua Security Best Practices](https://www.lua.org/manual/5.4/manual.html#6.2)
- [Xring Obfuscator Analysis](https://github.com/security-research)
- [Moonsec Analysis Documentation](https://github.com/blacktrace/moonsec)
- [Malware Analysis Techniques](https://www.alephsecurity.com/papers/)

## 🔗 Related Tools

- [Lua Static Analysis](https://www.lua.com)
- [SBCL Compiler](https://sbcl.sourceforge.io/)
- [LuaJIT](https://luajit.org/)

---

**Last Updated**: November 2026
**License**: Educational/Security Use Only

*"Security through detection, not absence of use."*