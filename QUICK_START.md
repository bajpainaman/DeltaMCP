# Quick Start - Claude Code

## 1. Add MCP Server to Claude Code

Copy this JSON into your Claude Code MCP settings:

```json
{
  "mcpServers": {
    "delta": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/namanbajpai/DeltaMCP",
        "run",
        "server.py"
      ],
      "env": {
        "GIT_CONFIG_GLOBAL": "~/.gitconfig"
      }
    }
  }
}
```

**Important:** Replace `/Users/namanbajpai/DeltaMCP` with your actual path. Get it by running:
```bash
cd /path/to/DeltaMCP && pwd
```

## 2. Restart Claude Code

Fully quit and restart Claude Code after adding the configuration.

## 3. Test It Works

Type these commands in Claude Code:

**Test 1 - Basic diff:**
```
Show me the diff for the last commit
```

**Test 2 - CLI mode:**
```
Show me the diff for HEAD in CLI mode
```

**Test 3 - Specific file:**
```
Format the git diff for server.py
```

**Test 4 - Side-by-side:**
```
Show me a side-by-side diff for HEAD~1
```

## 4. Verify MCP is Connected

If Claude responds with formatted, syntax-highlighted diffs, it's working! You should see:
- Side-by-side diff format (left/right split)
- Syntax highlighting
- Line numbers
- Clean terminal output

If it doesn't work:
- Check that delta is installed: `delta --version`
- Check Claude Code logs for MCP errors
- Verify the path in the config is absolute and correct
- Make sure you fully restarted Claude Code

