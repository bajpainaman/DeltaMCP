"""Configuration management for Delta settings."""
import configparser
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class DeltaConfigManager:
    """Manages Delta configuration from Git config files."""
    
    def __init__(self, git_config_path: Optional[str] = None):
        """Initialize config manager.
        
        Args:
            git_config_path: Path to Git config file (default: ~/.gitconfig or GIT_CONFIG_GLOBAL)
        """
        self.config = configparser.ConfigParser()
        self.git_config_path = git_config_path or self._find_git_config()
        self._load_config()
    
    def _find_git_config(self) -> Path:
        """Find Git config file path.
        
        Returns:
            Path to Git config file
        """
        # Check GIT_CONFIG_GLOBAL environment variable first
        env_config = os.environ.get("GIT_CONFIG_GLOBAL")
        if env_config:
            config_path = Path(env_config).expanduser()
            if config_path.exists():
                return config_path
        
        # Default to ~/.gitconfig
        default_path = Path.home() / ".gitconfig"
        return default_path
    
    def _load_config(self) -> None:
        """Load configuration from Git config file."""
        config_path = Path(self.git_config_path).expanduser()
        
        if not config_path.exists():
            logger.debug(f"Git config file not found: {config_path}")
            return
        
        try:
            # Git config uses INI-like format but with some quirks
            # configparser can handle it with some adjustments
            with open(config_path, 'r', encoding='utf-8') as f:
                # Read and parse the config
                self.config.read_file(f)
        except Exception as e:
            logger.warning(f"Error loading Git config: {e}")
    
    def get_delta_config(self) -> Dict[str, Any]:
        """Get Delta configuration from [delta] section.
        
        Returns:
            Dictionary of Delta configuration options
        """
        delta_config = {}
        
        if 'delta' in self.config:
            delta_section = self.config['delta']
            for key, value in delta_section.items():
                # Git config values are often quoted, remove quotes
                cleaned_value = value.strip('"\'')
                
                # Convert boolean strings
                if cleaned_value.lower() in ('true', 'yes', '1'):
                    delta_config[key] = True
                elif cleaned_value.lower() in ('false', 'no', '0'):
                    delta_config[key] = False
                else:
                    delta_config[key] = cleaned_value
        
        return delta_config
    
    def get_option(self, option: str, default: Any = None) -> Any:
        """Get a specific Delta configuration option.
        
        Args:
            option: Option name (e.g., "syntax-theme")
            default: Default value if option not found
            
        Returns:
            Option value or default
        """
        delta_config = self.get_delta_config()
        return delta_config.get(option, default)
    
    def merge_with_overrides(self, overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Merge file config with parameter overrides.
        
        Args:
            overrides: Dictionary of configuration overrides
            
        Returns:
            Merged configuration dictionary
        """
        base_config = self.get_delta_config()
        # Overrides take precedence
        merged = {**base_config, **overrides}
        return merged


# Global config manager instance
_config_manager: Optional[DeltaConfigManager] = None


def get_config_manager(git_config_path: Optional[str] = None) -> DeltaConfigManager:
    """Get or create global config manager instance.
    
    Args:
        git_config_path: Optional path to Git config file
        
    Returns:
        DeltaConfigManager instance
    """
    global _config_manager
    
    if _config_manager is None or git_config_path:
        _config_manager = DeltaConfigManager(git_config_path)
    
    return _config_manager

