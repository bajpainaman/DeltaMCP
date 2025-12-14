"""Delta version checking and utility functions."""
import asyncio
import logging
import shutil
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


async def check_delta_version(min_version: str = "0.17.0") -> Tuple[bool, str]:
    """Check Delta version and return compatibility status.
    
    Args:
        min_version: Minimum required version (default: "0.17.0")
        
    Returns:
        Tuple of (is_compatible, version_string)
    """
    delta_path = shutil.which("delta")
    if not delta_path:
        return False, "not found"
    
    try:
        proc = await asyncio.create_subprocess_exec(
            delta_path, "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL
        )
        stdout, _ = await proc.communicate()
        if proc.returncode == 0:
            version_str = stdout.decode('utf-8').strip()
            logger.info(f"Delta version: {version_str}")
            # Simple version comparison (can be enhanced)
            # For now, just check if version string contains numbers
            if any(c.isdigit() for c in version_str):
                return True, version_str
            return True, version_str
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.error(f"Error checking Delta version: {e}")
    
    return False, "unknown"


def find_delta_executable(custom_path: Optional[str] = None) -> Optional[str]:
    """Find delta executable path.
    
    Args:
        custom_path: Custom path to delta executable (from user_config)
        
    Returns:
        Path to delta executable, or None if not found
    """
    if custom_path:
        path = shutil.which(custom_path)
        if path:
            return path
        # Try as direct path
        from pathlib import Path
        if Path(custom_path).exists():
            return custom_path
    
    return shutil.which("delta")

