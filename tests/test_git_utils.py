"""Tests for git utilities."""
import pytest
import asyncio
from pathlib import Path
from git_utils import is_git_repo, get_git_repo_root


@pytest.mark.asyncio
async def test_is_git_repo_not_repo(tmp_path):
    """Test git repo detection in non-repo directory."""
    result = await is_git_repo(tmp_path)
    assert result is False


@pytest.mark.asyncio
async def test_get_git_repo_root_not_repo(tmp_path):
    """Test getting git repo root in non-repo directory."""
    result = await get_git_repo_root(tmp_path)
    assert result is None

