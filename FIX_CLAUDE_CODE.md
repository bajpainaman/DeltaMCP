# Fix Claude Code Connection

## Problem
The MCP server fails because `uv` is not in your PATH.

## Solution: Use Python Directly

Remove the old config and add it with the full Python path:

```bash
# Remove old config
claude mcp remove delta

# Add with full Python path (no uv needed)
claude mcp add delta --transport stdio --env GIT_CONFIG_GLOBAL=~/.gitconfig -- /Users/namanbajpai/DeltaMCP/.venv/bin/python3 /Users/namanbajpai/DeltaMCP/server.py
```

**Replace `/Users/namanbajpai/DeltaMCP` with your actual path!**

## Alternative: Install uv

If you prefer to use `uv`, install it first:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then restart your terminal and use the original command.

## Verify

After adding, check it's working:
```bash
claude mcp list
```

Then in Claude Code, type:
```
Show me the diff for the last commit
```

