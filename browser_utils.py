"""Simplified browser integration for Delta MCP - uses static HTML files and terminal hyperlinks."""
import hashlib
import html
import logging
import re
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Cache directory for HTML files
CACHE_DIR = Path.home() / '.delta_mcp_cache'
CACHE_DIR.mkdir(exist_ok=True)


def _ansi_to_html(ansi_text: str) -> str:
    """Convert ANSI color codes to HTML with inline styles.
    Properly handles 256-color codes (38;5;X and 48;5;X) used by delta."""
    # Escape HTML first
    html_text = html.escape(ansi_text)
    
    # Pattern for ANSI escape sequences (including 256-color codes)
    ansi_pattern = re.compile(r'\x1b\[([0-9;]+)m')
    
    # Basic 8/16 color mapping
    color_map = {
        30: '#000000', 31: '#cd3131', 32: '#0dbc79', 33: '#e5e510',
        34: '#2472c8', 35: '#bc3fbc', 36: '#11a8cd', 37: '#e5e5e5',
        90: '#666666', 91: '#f14c4c', 92: '#23d18b', 93: '#f5f543',
        94: '#3b8eea', 95: '#d670d6', 96: '#29b8db', 97: '#e5e5e5',
    }
    
    bg_color_map = {
        40: '#000000', 41: '#cd3131', 42: '#0dbc79', 43: '#e5e510',
        44: '#2472c8', 45: '#bc3fbc', 46: '#11a8cd', 47: '#e5e5e5',
        100: '#666666', 101: '#f14c4c', 102: '#23d18b', 103: '#f5f543',
        104: '#3b8eea', 105: '#d670d6', 106: '#29b8db', 107: '#e5e5e5',
    }
    
    def ansi256_to_hex(color_code: int) -> str:
        """Convert 256-color ANSI code to hex color."""
        if 0 <= color_code <= 15:
            # Standard colors
            standard = ['#000000', '#800000', '#008000', '#808000',
                       '#000080', '#800080', '#008080', '#c0c0c0',
                       '#808080', '#ff0000', '#00ff00', '#ffff00',
                       '#0000ff', '#ff00ff', '#00ffff', '#ffffff']
            return standard[color_code]
        elif 16 <= color_code <= 231:
            # 6x6x6 color cube
            r = (color_code - 16) // 36
            g = ((color_code - 16) % 36) // 6
            b = (color_code - 16) % 6
            r = 55 + r * 40 if r > 0 else 0
            g = 55 + g * 40 if g > 0 else 0
            b = 55 + b * 40 if b > 0 else 0
            return f'#{r:02x}{g:02x}{b:02x}'
        elif 232 <= color_code <= 255:
            # Grayscale
            gray = 8 + (color_code - 232) * 10
            return f'#{gray:02x}{gray:02x}{gray:02x}'
        return '#ffffff'
    
    parts = []
    span_stack = []  # Track open spans for proper nesting
    last_pos = 0
    
    for match in ansi_pattern.finditer(html_text):
        if match.start() > last_pos:
            parts.append(html_text[last_pos:match.start()])
        
        codes_str = match.group(1)
        codes = [int(c) if c else 0 for c in codes_str.split(';')]
        
        i = 0
        while i < len(codes):
            code = codes[i]
            
            if code == 0:  # Reset - close all open spans
                while span_stack:
                    parts.append('</span>')
                    span_stack.pop()
            elif code == 1:  # Bold
                styles = ['font-weight: bold']
                parts.append(f'<span style="{"; ".join(styles)}">')
                span_stack.append(styles)
            elif code == 4:  # Underline
                styles = ['text-decoration: underline']
                parts.append(f'<span style="{"; ".join(styles)}">')
                span_stack.append(styles)
            elif code == 7:  # Reverse video (invert)
                # Skip for now
                pass
            elif code in color_map:
                styles = [f'color: {color_map[code]}']
                parts.append(f'<span style="{"; ".join(styles)}">')
                span_stack.append(styles)
            elif code in bg_color_map:
                styles = [f'background-color: {bg_color_map[code]}']
                parts.append(f'<span style="{"; ".join(styles)}">')
                span_stack.append(styles)
            elif code == 38 and i + 2 < len(codes) and codes[i+1] == 5:
                # 256-color foreground: 38;5;X
                color_code = codes[i+2]
                hex_color = ansi256_to_hex(color_code)
                styles = [f'color: {hex_color}']
                parts.append(f'<span style="{"; ".join(styles)}">')
                span_stack.append(styles)
                i += 2  # Skip the next two codes
            elif code == 48 and i + 2 < len(codes) and codes[i+1] == 5:
                # 256-color background: 48;5;X
                color_code = codes[i+2]
                hex_color = ansi256_to_hex(color_code)
                styles = [f'background-color: {hex_color}']
                parts.append(f'<span style="{"; ".join(styles)}">')
                span_stack.append(styles)
                i += 2  # Skip the next two codes
            
            i += 1
        
        last_pos = match.end()
    
    if last_pos < len(html_text):
        parts.append(html_text[last_pos:])
    
    # Close any remaining open spans
    while span_stack:
        parts.append('</span>')
        span_stack.pop()
    
    result = ''.join(parts)
    return f'<pre style="font-family: \'SF Mono\', Monaco, \'Cascadia Code\', Consolas, monospace; background: #1e1e1e; color: #d4d4d4; padding: 20px; border-radius: 8px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; line-height: 1.5;">{result}</pre>'


def _create_html_page(title: str, content: str, theme: str | None = None) -> str:
    """Create a complete HTML page."""
    # Default to dark theme for HTML (delta's ANSI colors are already applied)
    # The theme parameter here is just for HTML page styling, not delta's syntax highlighting
    bg_color = "#1e1e1e"  # Dark background to match delta's typical output
    text_color = "#d4d4d4"  # Light text for readability
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: {bg_color};
            color: {text_color};
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            border-bottom: 2px solid #444;
            padding-bottom: 10px;
            margin-bottom: 20px;
            font-size: 24px;
        }}
        .meta {{
            background: #2d2d2d;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #007acc;
            font-size: 14px;
        }}
        pre {{
            margin: 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{html.escape(title)}</h1>
        <div class="meta">
            <strong>Delta MCP Server</strong> - Formatted with git-delta
        </div>
        {content}
    </div>
</body>
</html>"""


def save_diff_to_browser(title: str, formatted_output: str, theme: str | None = None) -> str:
    """
    Save formatted diff to HTML file and return file:// URL.
    This is simpler and more reliable than HTTP server.
    
    Args:
        title: Title for the HTML page
        formatted_output: ANSI-formatted diff output
        theme: Theme name (optional - defaults to "dark" for HTML styling, but delta uses its own theme)
    
    Returns:
        file:// URL that can be opened directly in browser
    """
    # Create hash for this diff
    diff_hash = hashlib.md5(f"{title}{formatted_output}".encode()).hexdigest()[:16]
    
    # Convert ANSI to HTML
    html_content = _ansi_to_html(formatted_output)
    
    # Create full HTML page
    full_html = _create_html_page(title, html_content, theme)
    
    # Save to file
    html_file = CACHE_DIR / f"{diff_hash}.html"
    try:
        html_file.write_text(full_html, encoding='utf-8')
        logger.info(f"Saved diff to {html_file}")
    except Exception as e:
        logger.error(f"Could not save HTML file: {e}")
        raise
    
    # Clean old files (keep last 50)
    try:
        html_files = sorted(CACHE_DIR.glob("*.html"), key=lambda p: p.stat().st_mtime, reverse=True)
        for old_file in html_files[50:]:
            try:
                old_file.unlink()
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"Could not clean old cache files: {e}")
    
    # Return file:// URL
    file_url = html_file.as_uri()
    return file_url


def create_terminal_hyperlink(text: str, uri: str) -> str:
    """
    Create a clickable hyperlink in terminal using OSC 8 escape sequence.
    
    Based on: https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
    Syntax: OSC 8 ; params ; URI ST text OSC 8 ;; ST
    
    Args:
        text: The visible text to display
        uri: The target URI (http://, https://, file://, etc.)
    
    Returns:
        Terminal escape sequence that creates a clickable link
    """
    # OSC 8 ; ; URI ST text OSC 8 ;; ST
    # OSC is ESC ] (\033])
    # ST is ESC \ (\033\\)
    return f"\033]8;;{uri}\033\\{text}\033]8;;\033\\"


def format_with_terminal_link(formatted_output: str, file_url: str, title: str) -> str:
    """
    Format output with terminal hyperlinks side-by-side at the top.
    Returns clean terminal output that looks like native delta, with clickable browser links.
    
    Args:
        formatted_output: The formatted diff output (with ANSI colors)
        file_url: The file:// URL to link to
        title: Title/description of the diff
    
    Returns:
        Formatted string with clickable terminal hyperlinks side-by-side - clean terminal-style output
        that works in both CLI and browser
    """
    # Create clickable link using OSC 8 (works in terminal, also shows URL for copy-paste)
    link_text = f"View in browser: {title}"
    terminal_link = create_terminal_hyperlink(link_text, file_url)
    
    # Return clean output with side-by-side links:
    # - Two clickable links side-by-side at top (OSC 8 hyperlinks)
    # - Clean formatted diff (looks exactly like native delta CLI output)
    # - Plain URL for easy copy-paste
    result = f"{terminal_link}  |  {terminal_link}\n\n{formatted_output}\n\nBrowser URL: {file_url}"
    
    return result


def get_browser_url(file_url: str) -> str:
    """
    Get a browser-friendly URL. Returns the file:// URL.
    Cursor and other clients can handle file:// URLs directly.
    """
    return file_url

