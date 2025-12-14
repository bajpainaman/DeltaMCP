"""Git repository detection and utility functions."""
import asyncio
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


async def is_git_repo(cwd: Path | None = None) -> bool:
    """Check if current directory is a git repository.
    
    Args:
        cwd: Working directory to check (default: current directory)
        
    Returns:
        True if in a git repository, False otherwise
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "rev-parse", "--is-inside-work-tree",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            cwd=cwd
        )
        await proc.wait()
        return proc.returncode == 0
    except FileNotFoundError:
        logger.warning("Git not found in PATH")
        return False
    except Exception as e:
        logger.error(f"Error checking git repo: {e}")
        return False


async def get_git_repo_root(cwd: Path | None = None) -> Path | None:
    """Get git repository root directory.
    
    Args:
        cwd: Working directory to start from (default: current directory)
        
    Returns:
        Path to git repository root, or None if not in a git repo
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "rev-parse", "--show-toplevel",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            cwd=cwd
        )
        stdout, _ = await proc.communicate()
        if proc.returncode == 0:
            return Path(stdout.decode('utf-8').strip())
        return None
    except FileNotFoundError:
        logger.warning("Git not found in PATH")
        return None
    except Exception as e:
        logger.error(f"Error getting git repo root: {e}")
        return None

