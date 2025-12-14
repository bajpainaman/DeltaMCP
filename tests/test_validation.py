"""Tests for input validation utilities."""
import pytest
from pathlib import Path
from validation import validate_path, validate_commit_range, validate_grep_tool, ALLOWED_GREP_TOOLS


def test_validate_commit_range():
    """Test commit range validation."""
    # Valid ranges
    assert validate_commit_range("HEAD") == "HEAD"
    assert validate_commit_range("HEAD~1") == "HEAD~1"
    assert validate_commit_range("abc123") == "abc123"
    assert validate_commit_range("abc123..def456") == "abc123..def456"
    
    # Invalid ranges
    with pytest.raises(ValueError):
        validate_commit_range("; rm -rf /")
    with pytest.raises(ValueError):
        validate_commit_range("HEAD | cat")


def test_validate_grep_tool():
    """Test grep tool whitelist validation."""
    # Valid tools
    for tool in ALLOWED_GREP_TOOLS:
        assert validate_grep_tool(tool) == tool
    
    # Invalid tools
    with pytest.raises(ValueError):
        validate_grep_tool("malicious-command")
    with pytest.raises(ValueError):
        validate_grep_tool("rm")


def test_validate_path_none():
    """Test path validation with None."""
    assert validate_path(None) is None


def test_validate_path_invalid():
    """Test path validation with invalid path."""
    with pytest.raises(ValueError):
        validate_path("/nonexistent/path/to/file.txt")


def test_validate_path_outside_repo(tmp_path):
    """Test path validation outside git repo."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("test")
    
    with pytest.raises(ValueError, match="outside git repository"):
        validate_path(str(outside_file), repo_root)

