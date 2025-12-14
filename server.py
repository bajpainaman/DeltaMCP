"""Main MCP server implementation for Delta."""
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, AsyncIterator

from mcp.server.fastmcp import FastMCP

# Configure logging to stderr (CRITICAL: never use stdout for STDIO servers)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Explicitly use stderr
)

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("delta-mcp")

# Import utilities
from delta_utils import check_delta_version, find_delta_executable
from git_utils import is_git_repo, get_git_repo_root
from validation import validate_path, validate_commit_range, validate_grep_tool
from config_manager import get_config_manager
from resources import register_resources
from browser_utils import save_diff_to_browser, get_browser_url, format_with_terminal_link
import webbrowser

# Check Delta on startup
_delta_version_checked = False
_delta_available = False


async def ensure_delta_available() -> bool:
    """Check if Delta is available and log version."""
    global _delta_version_checked, _delta_available
    
    if not _delta_version_checked:
        is_compatible, version = await check_delta_version()
        _delta_available = is_compatible
        _delta_version_checked = True
        
        if is_compatible:
            logger.info(f"Delta available: {version}")
        else:
            logger.warning(f"Delta not available: {version}")
    
    return _delta_available


@mcp.tool()
async def format_git_show(
    commit_hash: str,
    file_path: str | None = None,
    theme: str | None = None,
    side_by_side: bool = True,  # Default: side-by-side diff format (left/right split)
    line_numbers: bool = True,
    open_in_browser: bool = True
) -> str:
    """
    Format git show output using Delta with syntax highlighting. 
    Returns clean terminal-style output (like native delta CLI) with optional browser links.
    
    Args:
        commit_hash: Git commit hash or reference (e.g., "HEAD", "abc123")
        file_path: Specific file to show (optional)
        theme: Syntax highlighting theme (optional - any bat/delta theme name, uses your config default if not specified)
        side_by_side: Enable side-by-side diff view
        line_numbers: Show line numbers
        open_in_browser: If True (default), includes clickable browser links; if False, returns only formatted text
    
    Returns:
        Clean terminal-formatted diff output with browser links (if open_in_browser=True) or plain formatted text
    """
    if not await ensure_delta_available():
        return "Error: Delta not installed. Install with: cargo install git-delta"
    
    # Validate commit hash
    try:
        commit_hash = validate_commit_range(commit_hash)
    except ValueError as e:
        return f"Error: {str(e)}"
    
    # Validate file path if provided
    git_repo_root = await get_git_repo_root()
    validated_path = None
    if file_path:
        try:
            validated_path = validate_path(file_path, git_repo_root)
        except ValueError as e:
            return f"Error: {str(e)}"
    
    # Get config and merge with overrides
    config_mgr = get_config_manager()
    config_overrides = {}
    if theme:
        config_overrides["syntax-theme"] = theme
    
    merged_config = config_mgr.merge_with_overrides(config_overrides)
    
    # Build git command
    git_cmd = ["git", "show", commit_hash]
    if validated_path:
        git_cmd.append("--")
        git_cmd.append(validated_path)
    
    # Build delta command with config
    # Default to unified diff format (like GitHub) unless side-by-side is explicitly requested
    delta_cmd = ["delta"]
    # Only add theme if explicitly provided - otherwise delta uses user's config/default
    if theme:
        delta_cmd.extend(["--syntax-theme", theme])
    elif merged_config.get("syntax-theme"):
        # Use theme from user's git config if available
        delta_cmd.extend(["--syntax-theme", merged_config.get("syntax-theme")])
    # Use side-by-side by default (left/right split view)
    if side_by_side or merged_config.get("side-by-side", True):
        delta_cmd.append("--side-by-side")
    if line_numbers or merged_config.get("line-numbers", True):
        delta_cmd.append("--line-numbers")
    
    # Execute: git show | delta
    from delta_wrapper import execute_git_then_delta
    formatted_output = await execute_git_then_delta(git_cmd, delta_cmd)
    
    # If browser link requested, create and return URL with terminal hyperlink
    if open_in_browser:
        title = f"Git Show: {commit_hash}"
        if validated_path:
            title += f" - {validated_path}"
        file_url = save_diff_to_browser(title, formatted_output, theme)
        browser_url = get_browser_url(file_url)
        
        # Try to open in browser
        try:
            webbrowser.open(browser_url)
            logger.info(f"Opened browser: {browser_url}")
        except Exception as e:
            logger.warning(f"Could not open browser: {e}")
        
        # Return clean terminal output with clickable hyperlink
        # Format: clean diff output + clickable link at top and bottom
        return format_with_terminal_link(formatted_output, browser_url, title)
    
    return formatted_output


@mcp.tool()
async def format_git_show_cli(
    commit_hash: str,
    file_path: str | None = None,
    theme: str | None = None,
    side_by_side: bool = True,
    line_numbers: bool = True
) -> str:
    """
    Format git show output using Delta - CLI only (no browser). 
    Designed for Claude Code and other CLI-focused clients.
    
    Args:
        commit_hash: Git commit hash or reference (e.g., "HEAD", "abc123")
        file_path: Specific file to show (optional)
        theme: Syntax highlighting theme (optional - uses your config default if not specified)
        side_by_side: Enable side-by-side diff view (default: True)
        line_numbers: Show line numbers (default: True)
    
    Returns:
        Clean terminal-formatted diff output (CLI only, no browser links)
    """
    # Use the same logic as format_git_show but with open_in_browser=False
    return await format_git_show(
        commit_hash=commit_hash,
        file_path=file_path,
        theme=theme,
        side_by_side=side_by_side,
        line_numbers=line_numbers,
        open_in_browser=False  # CLI only
    )


@mcp.tool()
async def format_git_log(
    limit: int = 10,
    author: str | None = None,
    since: str | None = None,
    until: str | None = None,
    file_path: str | None = None,
    theme: str | None = None,
    side_by_side: bool = True,  # Default: side-by-side format (left/right split)
    line_numbers: bool = True,
    hyperlinks: bool = False,
    width: int | None = None,
    max_line_length: int | None = None,
    max_line_distance: int | None = None,
    open_in_browser: bool = True
) -> str:
    """
    Format git log with patches using Delta. 
    Returns clean terminal-style output (like native delta CLI) with optional browser links.
    Works in both CLI and browser - output looks like native delta with clickable browser links.
    
    Args:
        limit: Number of commits to show (default: 10)
        author: Filter by author name or email
        since: Show commits after this date (ISO format or relative)
        until: Show commits before this date (ISO format or relative)
        file_path: Filter commits that touch this file
        theme: Syntax highlighting theme (optional - any bat/delta theme name, uses your config default if not specified)
        side_by_side: Enable side-by-side diff view
        line_numbers: Show line numbers
        open_in_browser: If True (default), includes clickable browser links; if False, returns only formatted text
    
    Returns:
        Clean terminal-formatted git log output with browser links (if open_in_browser=True) or plain formatted text
    """
    if not await ensure_delta_available():
        return "Error: Delta not installed. Install with: cargo install git-delta"
    
    # Validate file path if provided
    git_repo_root = await get_git_repo_root()
    validated_path = None
    if file_path:
        try:
            validated_path = validate_path(file_path, git_repo_root)
        except ValueError as e:
            return f"Error: {str(e)}"
    
    # Get config
    config_mgr = get_config_manager()
    config_overrides = {}
    if theme:
        config_overrides["syntax-theme"] = theme
    
    merged_config = config_mgr.merge_with_overrides(config_overrides)
    
    # Build git command
    git_cmd = ["git", "log", "-p", f"-{limit}"]
    if author:
        git_cmd.extend(["--author", author])
    if since:
        git_cmd.extend(["--since", since])
    if until:
        git_cmd.extend(["--until", until])
    if validated_path:
        git_cmd.append("--")
        git_cmd.append(validated_path)
    
    # Build delta command with all supported flags
    delta_cmd = ["delta"]
    # Only add theme if explicitly provided - otherwise delta uses user's config/default
    if theme:
        delta_cmd.extend(["--syntax-theme", theme])
    elif merged_config.get("syntax-theme"):
        # Use theme from user's git config if available
        delta_cmd.extend(["--syntax-theme", merged_config.get("syntax-theme")])
    if side_by_side or merged_config.get("side-by-side", True):
        delta_cmd.append("--side-by-side")
    if line_numbers or merged_config.get("line-numbers", True):
        delta_cmd.append("--line-numbers")
    if hyperlinks or merged_config.get("hyperlinks"):
        delta_cmd.append("--hyperlinks")
    if width:
        delta_cmd.extend(["--width", str(width)])
    if max_line_length:
        delta_cmd.extend(["--max-line-length", str(max_line_length)])
    if max_line_distance:
        delta_cmd.extend(["--max-line-distance", str(max_line_distance)])
    
    # Execute: git log | delta
    from delta_wrapper import execute_git_then_delta
    formatted_output = await execute_git_then_delta(git_cmd, delta_cmd)
    
    # If browser link requested, create and return URL
    if open_in_browser:
        title = "Git Log"
        if file_path:
            title += f" - {file_path}"
        if author:
            title += f" by {author}"
        file_url = save_diff_to_browser(title, formatted_output, theme)
        browser_url = get_browser_url(file_url)
        
        try:
            webbrowser.open(browser_url)
            logger.info(f"Opened browser: {browser_url}")
        except Exception as e:
            logger.warning(f"Could not open browser: {e}")
        
        # Return with terminal hyperlink (OSC 8) - clickable in terminal!
        return format_with_terminal_link(formatted_output, browser_url, title)
    
    return formatted_output


@mcp.tool()
async def format_git_diff_cli(
    file_path: str | None = None,
    commit_range: str | None = None,
    staged: bool = False,
    theme: str | None = None,
    side_by_side: bool = True,
    line_numbers: bool = True
) -> str:
    """
    Format git diff output using Delta - CLI only (no browser).
    Designed for Claude Code and other CLI-focused clients.
    
    Args:
        file_path: Specific file to diff (optional, diffs all if not provided)
        commit_range: Git commit range (e.g., "HEAD~1..HEAD" or "abc123..def456")
        staged: If True, show staged changes; if False, show unstaged
        theme: Syntax highlighting theme (optional - uses your config default if not specified)
        side_by_side: Enable side-by-side diff view (default: True)
        line_numbers: Show line numbers (default: True)
    
    Returns:
        Clean terminal-formatted diff output (CLI only, no browser links)
    """
    return await format_git_diff(
        file_path=file_path,
        commit_range=commit_range,
        staged=staged,
        theme=theme,
        side_by_side=side_by_side,
        line_numbers=line_numbers,
        open_in_browser=False  # CLI only
    )


@mcp.tool()
async def format_git_diff(
    file_path: str | None = None,
    commit_range: str | None = None,
    staged: bool = False,
    theme: str | None = None,
    side_by_side: bool = True,  # Default: side-by-side format (left/right split)
    line_numbers: bool = True,
    hyperlinks: bool = False,
    width: int | None = None,
    tabs: int | None = None,
    dark: bool = False,
    light: bool = False,
    max_line_length: int | None = None,
    max_line_distance: int | None = None,
    open_in_browser: bool = True
) -> str:
    """
    Format git diff output using Delta with syntax highlighting. 
    Returns clean terminal-style output (like native delta CLI) with optional browser links.
    Works in both CLI and browser - output looks like native delta with clickable browser links.
    
    Args:
        file_path: Specific file to diff (optional, diffs all if not provided)
        commit_range: Git commit range (e.g., "HEAD~1..HEAD" or "abc123..def456")
        staged: If True, show staged changes; if False, show unstaged
        theme: Syntax highlighting theme (optional - any bat/delta theme name, uses your config default if not specified)
        side_by_side: Enable side-by-side diff view
        line_numbers: Show line numbers
        open_in_browser: If True (default), includes clickable browser links; if False, returns only formatted text
    
    Returns:
        Clean terminal-formatted diff output with browser links (if open_in_browser=True) or plain formatted text
    """
    if not await ensure_delta_available():
        return "Error: Delta not installed. Install with: cargo install git-delta"
    
    # Validate inputs
    git_repo_root = await get_git_repo_root()
    validated_path = None
    if file_path:
        try:
            validated_path = validate_path(file_path, git_repo_root)
        except ValueError as e:
            return f"Error: {str(e)}"
    
    if commit_range:
        try:
            commit_range = validate_commit_range(commit_range)
        except ValueError as e:
            return f"Error: {str(e)}"
    
    # Build git command
    git_cmd = ["git", "diff"]
    if staged:
        git_cmd.append("--staged")
    if commit_range:
        git_cmd.append(commit_range)
    if validated_path:
        git_cmd.append("--")
        git_cmd.append(validated_path)
    
    # Get config and merge with overrides
    config_mgr = get_config_manager()
    config_overrides = {}
    if theme:
        config_overrides["syntax-theme"] = theme
    
    merged_config = config_mgr.merge_with_overrides(config_overrides)
    
    # Build delta command with all supported flags
    delta_cmd = ["delta"]
    # Only add theme if explicitly provided - otherwise delta uses user's config/default
    if theme:
        delta_cmd.extend(["--syntax-theme", theme])
    elif merged_config.get("syntax-theme"):
        # Use theme from user's git config if available
        delta_cmd.extend(["--syntax-theme", merged_config.get("syntax-theme")])
    if side_by_side or merged_config.get("side-by-side", True):
        delta_cmd.append("--side-by-side")
    if line_numbers or merged_config.get("line-numbers", True):
        delta_cmd.append("--line-numbers")
    if hyperlinks or merged_config.get("hyperlinks"):
        delta_cmd.append("--hyperlinks")
    if width:
        delta_cmd.extend(["--width", str(width)])
    if tabs:
        delta_cmd.extend(["--tabs", str(tabs)])
    if dark:
        delta_cmd.append("--dark")
    if light:
        delta_cmd.append("--light")
    if max_line_length:
        delta_cmd.extend(["--max-line-length", str(max_line_length)])
    if max_line_distance:
        delta_cmd.extend(["--max-line-distance", str(max_line_distance)])
    
    # Execute: git diff | delta
    from delta_wrapper import execute_git_then_delta
    formatted_output = await execute_git_then_delta(git_cmd, delta_cmd)
    
    # If browser link requested, create and return URL
    if open_in_browser:
        title = "Git Diff"
        if commit_range:
            title += f" - {commit_range}"
        if validated_path:
            title += f" - {validated_path}"
        file_url = save_diff_to_browser(title, formatted_output, theme)
        browser_url = get_browser_url(file_url)
        
        try:
            webbrowser.open(browser_url)
            logger.info(f"Opened browser: {browser_url}")
        except Exception as e:
            logger.warning(f"Could not open browser: {e}")
        
        # Return with terminal hyperlink (OSC 8) - clickable in terminal!
        return format_with_terminal_link(formatted_output, browser_url, title)
    
    return formatted_output


@mcp.tool()
async def format_git_blame(
    file_path: str,
    line_range: str | None = None,
    theme: str | None = None,
    line_numbers: bool = True
) -> str:
    """
    Format git blame output using Delta with syntax highlighting.
    
    Args:
        file_path: File to show blame for
        line_range: Optional line range (e.g., "10-20" or "10,+5")
        theme: Syntax highlighting theme
        line_numbers: Show line numbers
    
    Returns:
        Formatted blame output ready for display
    """
    if not await ensure_delta_available():
        return "Error: Delta not installed. Install with: cargo install git-delta"
    
    # Validate file path
    git_repo_root = await get_git_repo_root()
    try:
        validated_path = validate_path(file_path, git_repo_root)
    except ValueError as e:
        return f"Error: {str(e)}"
    
    # Get config
    config_mgr = get_config_manager()
    config_overrides = {}
    if theme:
        config_overrides["syntax-theme"] = theme
    
    merged_config = config_mgr.merge_with_overrides(config_overrides)
    
    # Build git command
    git_cmd = ["git", "blame"]
    if line_range:
        git_cmd.extend(["-L", line_range])
    git_cmd.append(validated_path)
    
    # Build delta command
    delta_cmd = ["delta"]
    # Only add theme if explicitly provided - otherwise delta uses user's config/default
    if theme:
        delta_cmd.extend(["--syntax-theme", theme])
    elif merged_config.get("syntax-theme"):
        # Use theme from user's git config if available
        delta_cmd.extend(["--syntax-theme", merged_config.get("syntax-theme")])
    if line_numbers or merged_config.get("line-numbers", True):
        delta_cmd.append("--line-numbers")
    
    # Execute: git blame | delta
    from delta_wrapper import execute_git_then_delta
    return await execute_git_then_delta(git_cmd, delta_cmd)


@mcp.tool()
async def format_grep_results(
    pattern: str,
    file_path: str | None = None,
    tool: str = "rg",
    theme: str | None = None,
    line_numbers: bool = True
) -> str:
    """
    Format grep/ripgrep output using Delta.
    
    Args:
        pattern: Search pattern
        file_path: Optional file or directory to search in
        tool: Tool to use - must be one of: grep, rg, git-grep (default: rg)
        theme: Syntax highlighting theme
        line_numbers: Show line numbers
    
    Returns:
        Formatted grep results ready for display
    """
    if not await ensure_delta_available():
        return "Error: Delta not installed. Install with: cargo install git-delta"
    
    # Validate tool
    try:
        tool = validate_grep_tool(tool)
    except ValueError as e:
        return f"Error: {str(e)}"
    
    # Validate file path if provided
    git_repo_root = await get_git_repo_root()
    validated_path = None
    if file_path:
        try:
            # For grep, path can be a directory too
            path_obj = Path(file_path).resolve()
            if path_obj.exists():
                validated_path = str(path_obj)
            else:
                return f"Error: Path does not exist: {file_path}"
        except Exception as e:
            return f"Error: Invalid path: {str(e)}"
    
    # Get config
    config_mgr = get_config_manager()
    config_overrides = {}
    if theme:
        config_overrides["syntax-theme"] = theme
    
    merged_config = config_mgr.merge_with_overrides(config_overrides)
    
    # Build grep command based on tool
    if tool == "rg":
        grep_cmd = ["rg", "--color=always", "--line-number", pattern]
        if validated_path:
            grep_cmd.append(validated_path)
    elif tool == "git-grep":
        grep_cmd = ["git", "grep", "-n", "--color=always", pattern]
        if validated_path:
            grep_cmd.append("--")
            grep_cmd.append(validated_path)
    else:  # grep
        grep_cmd = ["grep", "-n", "--color=always", pattern]
        if validated_path:
            grep_cmd.append(validated_path)
    
    # Build delta command
    delta_cmd = ["delta"]
    # Only add theme if explicitly provided - otherwise delta uses user's config/default
    if theme:
        delta_cmd.extend(["--syntax-theme", theme])
    elif merged_config.get("syntax-theme"):
        # Use theme from user's git config if available
        delta_cmd.extend(["--syntax-theme", merged_config.get("syntax-theme")])
    if line_numbers or merged_config.get("line-numbers", True):
        delta_cmd.append("--line-numbers")
    
    # Execute: grep | delta
    from delta_wrapper import execute_git_then_delta
    return await execute_git_then_delta(grep_cmd, delta_cmd)


@mcp.tool()
async def format_merge_conflicts(
    file_path: str | None = None,
    theme: str | None = None,
    side_by_side: bool = True,  # Default: side-by-side format (left/right split)
    line_numbers: bool = True
) -> str:
    """
    Format merge conflicts using Delta.
    
    Args:
        file_path: Optional specific file with conflicts
        theme: Syntax highlighting theme
        side_by_side: Enable side-by-side view
        line_numbers: Show line numbers
    
    Returns:
        Formatted merge conflict output ready for display
    """
    if not await ensure_delta_available():
        return "Error: Delta not installed. Install with: cargo install git-delta"
    
    # Validate file path if provided
    git_repo_root = await get_git_repo_root()
    validated_path = None
    if file_path:
        try:
            validated_path = validate_path(file_path, git_repo_root)
        except ValueError as e:
            return f"Error: {str(e)}"
    
    # Get config
    config_mgr = get_config_manager()
    config_overrides = {}
    if theme:
        config_overrides["syntax-theme"] = theme
    
    merged_config = config_mgr.merge_with_overrides(config_overrides)
    
    # Build git command for merge conflicts
    git_cmd = ["git", "diff", "--merge"]
    if validated_path:
        git_cmd.append("--")
        git_cmd.append(validated_path)
    
    # Build delta command
    delta_cmd = ["delta"]
    # Only add theme if explicitly provided - otherwise delta uses user's config/default
    if theme:
        delta_cmd.extend(["--syntax-theme", theme])
    elif merged_config.get("syntax-theme"):
        # Use theme from user's git config if available
        delta_cmd.extend(["--syntax-theme", merged_config.get("syntax-theme")])
    if side_by_side or merged_config.get("side-by-side", True):
        delta_cmd.append("--side-by-side")
    if line_numbers or merged_config.get("line-numbers", True):
        delta_cmd.append("--line-numbers")
    
    # Execute: git diff --merge | delta
    from delta_wrapper import execute_git_then_delta
    return await execute_git_then_delta(git_cmd, delta_cmd)


@mcp.tool()
async def syntax_highlight_code(
    code: str,
    language: str | None = None,
    theme: str | None = None
) -> str:
    """
    Syntax highlight code snippets using Delta.
    
    Args:
        code: Code to highlight
        language: Programming language (auto-detect if not provided)
        theme: Syntax highlighting theme
    
    Returns:
        Syntax-highlighted code ready for display
    """
    if not await ensure_delta_available():
        return "Error: Delta not installed. Install with: cargo install git-delta"
    
    # Validate language if provided
    from validation import validate_language
    if language:
        try:
            language = validate_language(language)
        except ValueError as e:
            return f"Error: {str(e)}"
    
    # Get config
    config_mgr = get_config_manager()
    config_overrides = {}
    if theme:
        config_overrides["syntax-theme"] = theme
    
    merged_config = config_mgr.merge_with_overrides(config_overrides)
    
    # Build delta command
    delta_cmd = ["delta", "--color-only"]
    if language:
        delta_cmd.extend(["--default-language", language])
    # Only add theme if explicitly provided - otherwise delta uses user's config/default
    if theme:
        delta_cmd.extend(["--syntax-theme", theme])
    elif merged_config.get("syntax-theme"):
        # Use theme from user's git config if available
        delta_cmd.extend(["--syntax-theme", merged_config.get("syntax-theme")])
    
    # Execute delta with code as input
    from delta_wrapper import safe_delta_execution
    return await safe_delta_execution(delta_cmd, input_text=code)


@mcp.tool()
async def open_diff_in_browser(
    commit_hash: str | None = None,
    file_path: str | None = None,
    theme: str | None = None,
    side_by_side: bool = True,  # Default: side-by-side format (left/right split)
    line_numbers: bool = True
) -> str:
    """
    Format a git diff/show and open it in a browser as a shareable link.
    
    Args:
        commit_hash: Git commit hash or reference (e.g., "HEAD", "HEAD~1", "abc123")
        file_path: Specific file to show (optional)
        theme: Syntax highlighting theme (optional - uses your delta config or system default if not specified)
        side_by_side: Enable side-by-side diff view
        line_numbers: Show line numbers
    
    Returns:
        Browser URL that can be opened to view the formatted diff
    """
    if not await ensure_delta_available():
        return "Error: Delta not installed. Install with: cargo install git-delta"
    
    # Use format_git_show to get the formatted output
    if commit_hash:
        formatted_output = await format_git_show(
            commit_hash=commit_hash,
            file_path=file_path,
            theme=theme,
            side_by_side=side_by_side,
            line_numbers=line_numbers,
            open_in_browser=False
        )
        
        if formatted_output.startswith("Error:"):
            return formatted_output
        
        # Create browser link
        title = f"Git Show: {commit_hash}"
        if file_path:
            title += f" - {file_path}"
        file_url = save_diff_to_browser(title, formatted_output, theme)
        browser_url = get_browser_url(file_url)
        
        try:
            webbrowser.open(browser_url)
            logger.info(f"Opened browser: {browser_url}")
        except Exception as e:
            logger.warning(f"Could not open browser: {e}")
        
        # Return with terminal hyperlink (OSC 8) - clickable in terminal!
        return format_with_terminal_link(formatted_output, browser_url, title)
    else:
        # Use format_git_diff for unstaged changes
        formatted_output = await format_git_diff(
            file_path=file_path,
            theme=theme,
            side_by_side=side_by_side,
            line_numbers=line_numbers
        )
        
        if formatted_output.startswith("Error:"):
            return formatted_output
        
        # Create browser link
        title = "Git Diff"
        if file_path:
            title += f" - {file_path}"
        file_url = save_diff_to_browser(title, formatted_output, theme)
        browser_url = get_browser_url(file_url)
        
        try:
            webbrowser.open(browser_url)
            logger.info(f"Opened browser: {browser_url}")
        except Exception as e:
            logger.warning(f"Could not open browser: {e}")
        
        # Return with terminal hyperlink (OSC 8) - clickable in terminal!
        return format_with_terminal_link(formatted_output, browser_url, title)


@mcp.tool()
async def compare_files(
    file1_path: str,
    file2_path: str,
    theme: str | None = None,
    side_by_side: bool = True,  # Default: side-by-side format (left/right split)
    line_numbers: bool = True
) -> str:
    """
    Compare two files side-by-side using Delta.
    
    Args:
        file1_path: Path to first file
        file2_path: Path to second file
        theme: Syntax highlighting theme
        side_by_side: Enable side-by-side view
        line_numbers: Show line numbers
    
    Returns:
        Formatted file comparison ready for display
    """
    if not await ensure_delta_available():
        return "Error: Delta not installed. Install with: cargo install git-delta"
    
    # Validate file paths
    git_repo_root = await get_git_repo_root()
    try:
        validated_path1 = validate_path(file1_path, git_repo_root)
        validated_path2 = validate_path(file2_path, git_repo_root)
    except ValueError as e:
        return f"Error: {str(e)}"
    
    # Get config
    config_mgr = get_config_manager()
    config_overrides = {}
    if theme:
        config_overrides["syntax-theme"] = theme
    
    merged_config = config_mgr.merge_with_overrides(config_overrides)
    
    # Build diff command (works even outside git repo)
    import subprocess
    try:
        diff_output = subprocess.run(
            ["diff", "-u", validated_path1, validated_path2],
            capture_output=True,
            text=True,
            timeout=10.0
        )
        
        # diff returns non-zero if files differ, which is expected
        diff_text = diff_output.stdout + diff_output.stderr
        
        # Build delta command
        delta_cmd = ["delta"]
        if theme or merged_config.get("syntax-theme"):
            delta_cmd.extend(["--syntax-theme", theme or merged_config.get("syntax-theme")])
        if side_by_side or merged_config.get("side-by-side"):
            delta_cmd.append("--side-by-side")
        if line_numbers or merged_config.get("line-numbers", True):
            delta_cmd.append("--line-numbers")
        
        # Execute delta with diff output
        from delta_wrapper import safe_delta_execution
        return await safe_delta_execution(delta_cmd, input_text=diff_text)
        
    except FileNotFoundError:
        return "Error: diff command not found. Please install diffutils."
    except subprocess.TimeoutExpired:
        return "Error: File comparison timed out."
    except Exception as e:
        logger.error(f"Error comparing files: {e}", exc_info=True)
        return f"Error: {str(e)}"


def main():
    """Initialize and run the MCP server."""
    # Check Delta availability on startup
    asyncio.run(ensure_delta_available())
    
    # Browser integration uses static HTML files (file:// URLs)
    # No HTTP server needed - simpler and more reliable
    from browser_utils import CACHE_DIR
    logger.info(f"Browser cache directory: {CACHE_DIR}")
    
    # Register resources
    register_resources(mcp)
    
    # Run the server with STDIO transport
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()

