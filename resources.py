"""MCP resources for Delta."""
import logging
import asyncio
import shutil
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from delta_wrapper import execute_git_then_delta
from git_utils import get_git_repo_root
from validation import validate_path, validate_commit_range
from config_manager import get_config_manager

logger = logging.getLogger(__name__)


def register_resources(mcp: FastMCP) -> None:
    """Register MCP resources with the server."""
    
    @mcp.resource("delta://diff/{commit_hash}")
    async def get_commit_diff(commit_hash: str) -> str:
        """Get formatted diff for a specific commit.
        
        Args:
            commit_hash: Git commit hash or reference
        """
        try:
            commit_hash = validate_commit_range(commit_hash)
        except ValueError as e:
            return f"Error: {str(e)}"
        
        git_cmd = ["git", "show", commit_hash]
        delta_cmd = ["delta"]
        
        config_mgr = get_config_manager()
        merged_config = config_mgr.merge_with_overrides({})
        
        if merged_config.get("syntax-theme"):
            delta_cmd.extend(["--syntax-theme", merged_config.get("syntax-theme")])
        if merged_config.get("side-by-side"):
            delta_cmd.append("--side-by-side")
        if merged_config.get("line-numbers", True):
            delta_cmd.append("--line-numbers")
        
        return await execute_git_then_delta(git_cmd, delta_cmd)
    
    @mcp.resource("delta://blame/{file_path}")
    async def get_file_blame(file_path: str) -> str:
        """Get formatted blame for a file.
        
        Args:
            file_path: Path to file
        """
        git_repo_root = await get_git_repo_root()
        try:
            validated_path = validate_path(file_path, git_repo_root)
        except ValueError as e:
            return f"Error: {str(e)}"
        
        git_cmd = ["git", "blame", validated_path]
        delta_cmd = ["delta"]
        
        config_mgr = get_config_manager()
        merged_config = config_mgr.merge_with_overrides({})
        
        if merged_config.get("syntax-theme"):
            delta_cmd.extend(["--syntax-theme", merged_config.get("syntax-theme")])
        if merged_config.get("line-numbers", True):
            delta_cmd.append("--line-numbers")
        
        return await execute_git_then_delta(git_cmd, delta_cmd)
    
    @mcp.resource("delta://grep/{pattern}")
    async def get_grep_results(pattern: str) -> str:
        """Get formatted grep results.
        
        Args:
            pattern: Search pattern
        """
        git_cmd = ["git", "grep", "-n", "--color=always", pattern]
        delta_cmd = ["delta"]
        
        config_mgr = get_config_manager()
        merged_config = config_mgr.merge_with_overrides({})
        
        if merged_config.get("syntax-theme"):
            delta_cmd.extend(["--syntax-theme", merged_config.get("syntax-theme")])
        if merged_config.get("line-numbers", True):
            delta_cmd.append("--line-numbers")
        
        return await execute_git_then_delta(git_cmd, delta_cmd)
    
    @mcp.resource("delta://config")
    async def get_delta_config() -> str:
        """Get current Delta configuration."""
        config_mgr = get_config_manager()
        delta_config = config_mgr.get_delta_config()
        
        if not delta_config:
            return "No Delta configuration found in Git config."
        
        # Format as readable text
        lines = ["Delta Configuration:"]
        for key, value in sorted(delta_config.items()):
            lines.append(f"  {key} = {value}")
        
        return "\n".join(lines)
    
    @mcp.resource("delta://themes")
    async def get_available_themes() -> str:
        """List available syntax highlighting themes."""
        # Delta uses bat's themes, try to get list from bat
        bat_path = shutil.which("bat")
        if bat_path:
            try:
                proc = await asyncio.create_subprocess_exec(
                    bat_path, "--list-themes",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL
                )
                stdout, _ = await proc.communicate()
                if proc.returncode == 0:
                    themes = stdout.decode('utf-8').strip().split('\n')
                    return "Available themes:\n" + "\n".join(f"  - {t}" for t in themes if t.strip())
            except Exception as e:
                logger.warning(f"Could not get themes from bat: {e}")
        
        # Fallback: common themes
        common_themes = [
            "github", "dracula", "monokai", "nord", "one-dark", "one-light",
            "solarized-dark", "solarized-light", "gruvbox-dark", "gruvbox-light"
        ]
        return "Available themes (common):\n" + "\n".join(f"  - {t}" for t in common_themes)

