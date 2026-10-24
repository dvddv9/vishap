# Vishap Claude (Bundle)

Security analysis for engineering materials (code, spec, logs, config) via Claude API (Anthropic SDK).

## What it does

Detects SQL injection (CWE-89), XSS (CWE-79), RCE (CWE-78), TOCTOU (CWE-367), path traversal (CWE-22), command injection (CWE-78).
Returns a structured Markdown report with CWE, STRIDE threat model, and recommendations.

## Usage

1. Install the plugin in Claude Desktop.
2. Configure:
   - **ANTHROPIC_API_KEY** = `sk-ant-...` (from https://console.anthropic.com/settings/keys)
   - **ANTHROPIC_MODEL** = `claude-sonnet-5-5` (or another model)
3. Ask Claude:
   > Use vishap-analyze to analyze: `db.execute(f"SELECT * FROM users WHERE name = '{name}'")`

## Examples

### 1. SQL injection (CWE-89)

Input:
```python
db.execute(f"SELECT * FROM users WHERE name = '{name}'")
```
Output: Critical SQL injection — `' OR '1'='1` returns all users. Fix: parameterized query.

### 2. XSS (CWE-79)

Input:
```jsx
<div dangerouslySetInnerHTML={{ __html: user.bio }} />
```
Output: Critical XSS — arbitrary JS execution. Fix: sanitize with DOMPurify.

### 3. Path traversal (CWE-22)

Input:
```python
open(os.path.join("/data", filename)).read()
```
Output: High — `../etc/passwd` reads arbitrary files. Fix: `os.path.realpath` + allowlist.

## Privacy

This plugin sends the material you provide to the Anthropic API for analysis.
No data is stored by the plugin itself.

## License

AGPL-3.0-or-later. See [LICENSE](LICENSE).
