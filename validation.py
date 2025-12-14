"""Input validation utilities for security and safety."""
from pathlib import Path
import re
from typing import Optional

ALLOWED_GREP_TOOLS = ["grep", "rg", "git-grep"]


def validate_path(file_path: str | None, git_repo_root: Path | None = None) -> str | None:
    """Validate and resolve file path, ensuring it's within git repo.
    
    Args:
        file_path: File path to validate
        git_repo_root: Optional git repository root to restrict paths to
        
    Returns:
        Resolved absolute path as string, or None if file_path is None
        
    Raises:
        ValueError: If path is invalid or outside git repository
    """
    if not file_path:
        return None
    
    try:
        # If git_repo_root is provided, resolve relative to it
        if git_repo_root:
            resolved = (git_repo_root / file_path).resolve()
            # Ensure it's still within the repo root (prevent path traversal)
            try:
                resolved.relative_to(git_repo_root.resolve())
            except ValueError:
                raise ValueError(f"File path outside git repository: {file_path}")
        else:
            resolved = Path(file_path).resolve()
    except (OSError, ValueError) as e:
        raise ValueError(f"Invalid file path: {file_path} - {e}")
    
    if not resolved.is_file():
        raise ValueError(f"Invalid file path (not a file): {file_path}")
    
    return str(resolved)


def validate_commit_range(commit_range: str) -> str:
    """Validate git commit range format.
    
    Args:
        commit_range: Git commit range to validate (e.g., "HEAD~1", "abc123..def456")
        
    Returns:
        Validated commit range string
        
    Raises:
        ValueError: If commit range format is invalid
    """
    # Allow: HEAD~1, abc123..def456, HEAD, HEAD~1..HEAD, etc.
    # Pattern allows alphanumeric, ~, ^, ., :, - and .. for ranges
    pattern = r'^[a-zA-Z0-9~^.:\-]+(\.\.[a-zA-Z0-9~^.:\-]+)?$'
    if not re.match(pattern, commit_range):
        raise ValueError(f"Invalid commit range format: {commit_range}")
    return commit_range


def validate_grep_tool(tool: str) -> str:
    """Validate grep tool is in whitelist.
    
    Args:
        tool: Tool name to validate
        
    Returns:
        Validated tool name
        
    Raises:
        ValueError: If tool is not in whitelist
    """
    if tool not in ALLOWED_GREP_TOOLS:
        raise ValueError(f"Tool must be one of {ALLOWED_GREP_TOOLS}, got: {tool}")
    return tool


def validate_language(language: str | None) -> str | None:
    """Validate programming language identifier.
    
    Args:
        language: Language identifier (e.g., "python", "javascript")
        
    Returns:
        Validated language or None
    """
    if not language:
        return None
    
    # Basic validation - alphanumeric and hyphens only
    if not re.match(r'^[a-zA-Z0-9\-]+$', language):
        raise ValueError(f"Invalid language identifier: {language}")
    
    return language.lower()

