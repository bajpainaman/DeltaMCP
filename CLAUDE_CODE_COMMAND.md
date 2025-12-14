# Claude Code - One Command Setup

## Add DeltaMCP Server

Run this command in your terminal:

```bash
claude mcp add delta --transport stdio --env GIT_CONFIG_GLOBAL=~/.gitconfig -- uv --directory /Users/namanbajpai/DeltaMCP run server.py
```

**Replace `/Users/namanbajpai/DeltaMCP` with your actual path!**

To get your path:
```bash
cd /path/to/DeltaMCP && pwd
```

## Verify It's Added

Check that it's configured:
```bash
claude mcp list
```

You should see `delta` in the list.

## Test It Works

In Claude Code, type:
```
Show me the diff for the last commit
```

Or:
```
Show me the diff for HEAD in CLI mode
```

## Remove If Needed

If you need to remove it:
```bash
claude mcp remove delta
```

