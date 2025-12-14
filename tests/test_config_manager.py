"""Tests for configuration manager."""
import pytest
import tempfile
from pathlib import Path
from config_manager import DeltaConfigManager


def test_config_manager_default_path():
    """Test config manager with default path."""
    mgr = DeltaConfigManager()
    assert mgr.git_config_path is not None


def test_config_manager_custom_path(tmp_path):
    """Test config manager with custom path."""
    config_file = tmp_path / "test.gitconfig"
    config_file.write_text("""
[delta]
    syntax-theme = "github"
    line-numbers = true
""")
    
    mgr = DeltaConfigManager(str(config_file))
    config = mgr.get_delta_config()
    
    assert config.get("syntax-theme") == "github"
    assert config.get("line-numbers") is True


def test_config_manager_merge_overrides(tmp_path):
    """Test config merging with overrides."""
    config_file = tmp_path / "test.gitconfig"
    config_file.write_text("""
[delta]
    syntax-theme = "github"
    line-numbers = true
""")
    
    mgr = DeltaConfigManager(str(config_file))
    overrides = {"syntax-theme": "dracula"}
    
    merged = mgr.merge_with_overrides(overrides)
    
    assert merged["syntax-theme"] == "dracula"  # Override takes precedence
    assert merged["line-numbers"] is True  # From file


def test_config_manager_nonexistent_file():
    """Test config manager with nonexistent file."""
    mgr = DeltaConfigManager("/nonexistent/config.gitconfig")
    config = mgr.get_delta_config()
    
    # Should return empty dict, not crash
    assert isinstance(config, dict)

