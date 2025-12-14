"""Delta command execution wrapper with proper async subprocess handling."""
import asyncio
import logging
from typing import Optional
import shutil

logger = logging.getLogger(__name__)

# Default timeout for delta operations (30 seconds)
DEFAULT_TIMEOUT = 30.0
# Maximum output size (100KB)
MAX_OUTPUT_SIZE = 100_000


async def safe_delta_execution(
    cmd: list[str],
    input_text: str | bytes | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    delta_path: Optional[str] = None
) -> str:
    """Safely execute delta with proper error handling.
    
    Args:
        cmd: Command and arguments for delta (e.g., ["delta", "--syntax-theme", "github"])
        input_text: Input text to pipe to delta (will be encoded if string)
        timeout: Timeout in seconds (default: 30.0)
        delta_path: Custom path to delta executable
        
    Returns:
        Formatted output from delta, or error message
    """
    # Find delta executable
    if delta_path:
        delta_exec = shutil.which(delta_path) or delta_path
    else:
        delta_exec = shutil.which("delta")
    
    if not delta_exec:
        return "Error: Delta not installed. Install with: cargo install git-delta"
    
    # Use custom delta path if provided
    if delta_path and delta_exec != cmd[0]:
        cmd = [delta_exec] + cmd[1:]
    elif not delta_path:
        cmd = [delta_exec] + cmd[1:]
    
    try:
        # CRITICAL: asyncio.create_subprocess_exec does NOT support text=True
        # Input must be encoded if provided as string
        input_bytes = None
        if input_text:
            if isinstance(input_text, str):
                input_bytes = input_text.encode('utf-8')
            else:
                input_bytes = input_text
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE if input_bytes else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Add timeout (November 2025 best practice)
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=input_bytes),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return "Error: Delta execution timed out"
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='replace') if stderr else "Unknown error"
            logger.error(f"Delta failed: {error_msg}")
            return f"Error: {error_msg or 'Delta execution failed'}"
        
        # Decode output (always bytes from subprocess)
        output = stdout.decode('utf-8', errors='replace')
        
        # Limit output size
        if len(output) > MAX_OUTPUT_SIZE:
            output = output[:MAX_OUTPUT_SIZE] + f"\n\n[Output truncated - {len(output)} bytes total]"
        
        return output
        
    except FileNotFoundError:
        return "Error: Delta not installed. Install with: cargo install git-delta"
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return f"Error: {str(e)}"


async def execute_git_then_delta(
    git_cmd: list[str],
    delta_cmd: list[str],
    timeout: float = DEFAULT_TIMEOUT,
    delta_path: Optional[str] = None
) -> str:
    """Execute git command and pipe output to delta.
    
    Args:
        git_cmd: Git command and arguments
        delta_cmd: Delta command and arguments
        timeout: Timeout in seconds
        delta_path: Custom path to delta executable
        
    Returns:
        Formatted output from delta, or error message
    """
    # Find delta executable
    if delta_path:
        delta_exec = shutil.which(delta_path) or delta_path
    else:
        delta_exec = shutil.which("delta")
    
    if not delta_exec:
        return "Error: Delta not installed. Install with: cargo install git-delta"
    
    # Update delta command with executable path
    if delta_path and delta_exec != delta_cmd[0]:
        delta_cmd = [delta_exec] + delta_cmd[1:]
    elif not delta_path:
        delta_cmd = [delta_exec] + delta_cmd[1:]
    
    try:
        # Execute: git <cmd> | delta <options>
        # First, get output from git
        git_process = await asyncio.create_subprocess_exec(
            *git_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Read git output first
        try:
            git_stdout, git_stderr = await asyncio.wait_for(
                git_process.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            git_process.kill()
            await git_process.wait()
            return "Error: Git command timed out."
        
        if git_process.returncode != 0:
            error_msg = git_stderr.decode('utf-8', errors='replace') if git_stderr else "Unknown error"
            logger.error(f"Git error: {error_msg}")
            return f"Error: Git command failed: {error_msg}"
        
        # Now pipe git output to delta
        git_output = git_stdout.decode('utf-8', errors='replace')
        
        # Execute delta with git output as input
        return await safe_delta_execution(delta_cmd, input_text=git_output, timeout=timeout, delta_path=None)
        
    except FileNotFoundError as e:
        if "git" in str(e).lower():
            return "Error: Git not found. Please install Git."
        return "Error: Delta not found. Install with: cargo install git-delta"
    except Exception as e:
        logger.error(f"Error in execute_git_then_delta: {e}", exc_info=True)
        return f"Error: {str(e)}"

