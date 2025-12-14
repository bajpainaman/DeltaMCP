# How to Use Delta MCP in Claude

This guide shows you how to use the Delta MCP server with Claude (Claude Code, Claude Desktop, Cursor, etc.).

## Quick Start

Once the MCP server is configured, you can ask Claude to format diffs using natural language. Here are some example prompts:

### Basic Usage

**Show a commit diff:**
```
Show me the diff for the last commit using delta
```

**Show a specific file diff:**
```
Format the diff for server.py using delta
```

**Show diff between commits:**
```
Show me the diff between HEAD~1 and HEAD
```

### CLI Mode (No Browser Links)

For Claude Code or when you want clean terminal output without browser links:

```
Show me the diff for HEAD in CLI mode
```

Or be explicit:
```
Use format_git_show with cli_mode=true to show the last commit
```

### Browser Mode (With Clickable Links)

For Cursor or Claude Desktop where you want browser links:

```
Show me the diff for HEAD and open it in the browser
```

Or:
```
Format the git diff for server.py with browser links
```

## Available Tools

### format_git_show
Shows a specific commit with syntax highlighting.

**Example prompts:**
- "Show me commit abc123"
- "Format git show for HEAD using delta"
- "Display the last commit with side-by-side view"

**Parameters:**
- `commit_hash`: The commit to show (e.g., "HEAD", "abc123")
- `file_path`: Optional specific file
- `theme`: Optional syntax theme
- `side_by_side`: Side-by-side view (default: true)
- `line_numbers`: Show line numbers (default: true)
- `cli_mode`: CLI-only output, no browser links (default: false)

### format_git_diff
Shows git diff with syntax highlighting.

**Example prompts:**
- "Show me the diff for server.py"
- "What changed in the last commit?"
- "Format the git diff with side-by-side view"

**Parameters:**
- `file_path`: Optional file to diff
- `commit_range`: Optional commit range (e.g., "HEAD~1..HEAD")
- `staged`: Show staged changes (default: false)
- `side_by_side`: Side-by-side view (default: true)
- `cli_mode`: CLI-only output, no browser links (default: false)

### format_git_show_cli
CLI-only version of format_git_show (no browser links).

**Example prompts:**
- "Show me HEAD in CLI mode"
- "Use CLI mode to show the last commit"

### format_git_diff_cli
CLI-only version of format_git_diff (no browser links).

**Example prompts:**
- "Show diff in CLI mode"
- "Format the diff for server.py in CLI mode"

## Mode Selection

**CLI Mode** (`cli_mode=True` or use `*_cli` tools):
- Clean terminal output
- No browser links
- Perfect for Claude Code
- Pure diff content only

**Browser Mode** (default):
- Terminal output with clickable browser links
- Auto-opens HTML file in browser
- Perfect for Cursor, Claude Desktop
- Includes terminal hyperlinks

## Example Conversations

### Example 1: Quick Diff Check
```
You: Show me what changed in the last commit

Claude: [Uses format_git_show with HEAD, shows formatted diff]
```

### Example 2: CLI Mode for Claude Code
```
You: Show me the diff for server.py in CLI mode

Claude: [Uses format_git_diff_cli or format_git_diff with cli_mode=True]
```

### Example 3: Browser Mode with Links
```
You: Format the diff and open it in browser

Claude: [Uses format_git_diff with open_in_browser=True, creates HTML and opens it]
```

### Example 4: Side-by-Side View
```
You: Show me a side-by-side diff for HEAD~1

Claude: [Uses format_git_show with side_by_side=True]
```

## Tips

1. **For Claude Code**: Always use `cli_mode=True` or the `*_cli` tools for clean output
2. **For Cursor/Claude Desktop**: Use default browser mode for clickable links
3. **Side-by-side is default**: All diffs show side-by-side by default (left/right split)
4. **Natural language works**: Just describe what you want, Claude will choose the right tool

## Troubleshooting

If Claude doesn't use the tools:
- Make sure the MCP server is properly configured
- Restart your client after configuration changes
- Try being more explicit: "Use the delta MCP tool to format this diff"

If you see errors:
- Check that delta is installed: `delta --version`
- Verify your git config has delta configured
- Check the client logs for MCP errors

