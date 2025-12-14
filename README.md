# Delta MCP Server

A Model Context Protocol server that brings git-delta's beautiful syntax highlighting and diff formatting to AI assistants like Cursor, Claude Desktop, and Warp. Instead of plain text diffs, you get colorized, syntax-highlighted output that makes code reviews and debugging much easier.

## What This Does

When you ask an AI assistant to show you a git diff or explain code changes, this server formats the output using git-delta. That means you get proper syntax highlighting, side-by-side comparisons, line numbers, and all the visual enhancements that make diffs readable. The server integrates seamlessly with MCP-compatible clients, so you can use natural language to request formatted diffs, blame information, grep results, and more.

The server also supports terminal hyperlinks, so when you view a diff in your terminal, you can click a link to open it in your browser for a better viewing experience. All formatted output is saved as HTML files that persist on disk, making it easy to share or bookmark specific diffs.

## Requirements

You'll need Python 3.10 or higher, and git-delta must be installed. The easiest way to install delta is with cargo: `cargo install git-delta`. You'll also need Git installed, and I recommend using uv for dependency management, though pip works fine too.

## Installation

There are a few ways to set this up depending on how you want to use it. For Claude Desktop users, there's an MCPB package that provides one-click installation. If you prefer pip, you can install it as a package. For development or custom setups, you can clone the repository and set it up manually.

For development setup, start by installing uv if you don't have it already. Then clone the repository, create a virtual environment with `uv venv`, activate it, and install the dependencies with `uv pip install -e .`. The server will be ready to run.

## Configuration

Delta uses Git's configuration format, so you configure it by adding a `[delta]` section to your `~/.gitconfig` file. You can set the syntax theme, enable side-by-side view, turn on line numbers, and configure other options. There's an example configuration file in the `config` directory that shows all the available options.

For MCP client configuration, you'll need to add the server to your client's configuration file. The exact location depends on which client you're using. For Claude Desktop, it's in the Application Support directory. For Cursor, you can use the UI-based setup in Settings, or manually edit the configuration file. Warp uses a similar JSON configuration format.

The key thing to remember is to use absolute paths, not relative ones. On Windows, make sure to use double backslashes or forward slashes in your paths. After making configuration changes, you need to fully quit and restart your client, not just close the window.

## Usage

Once configured, you can use natural language to interact with the server through your AI assistant. Ask it to show you the formatted diff for a specific commit, format the git log with patches, search for patterns in your codebase, or compare two files. The server handles all the formatting automatically.

The server provides several tools that your AI assistant can use. These include formatting git diffs, showing commit details, displaying git log with patches, showing blame information, formatting grep results, displaying merge conflicts, syntax highlighting code snippets, and comparing files directly.

There are also resources available that provide direct access to formatted data. You can access formatted diffs for specific commits, blame information for files, grep results for patterns, your current delta configuration, and a list of available syntax themes.

## Security

The server includes input validation to prevent common security issues. File paths are validated to ensure they're within the git repository or current working directory, preventing path traversal attacks. Commit ranges are validated using regex patterns. Grep tools are restricted to a whitelist of safe tools: grep, ripgrep, and git-grep.

## Troubleshooting

If you see an error about Delta not being found, make sure you've installed it with `cargo install git-delta`. You can verify the installation by running `delta --version`. If you have delta installed in a non-standard location, you can configure the path in the MCPB manifest.

If your Git configuration isn't loading, check that your `~/.gitconfig` file exists and has the correct syntax. Delta uses INI format, not TOML. You can also set the `GIT_CONFIG_GLOBAL` environment variable to point to a different config file.

When the server doesn't show up in your client, the most common issues are invalid JSON in the configuration file, using relative paths instead of absolute ones, or not fully restarting the client after making changes. Make sure to completely quit the application, not just close the window.

If tool calls are failing, check the client's log files. For Claude Desktop, logs are in the Logs directory. You can also test the server manually by running `uv run server.py` to see if there are any errors.

## Development

To run the test suite, install the development dependencies with `uv pip install -e ".[dev]"` and then run `pytest`. The tests cover validation, configuration management, and git utilities.

To build an MCPB package for distribution, install the MCPB CLI as a dev dependency with npm, then run `npx @anthropic-ai/mcpb pack` to create the bundle file.

For building a pip package, use `python -m build` to create the distribution files, then upload them with `twine upload dist/*`.

## License

This project is licensed under the MIT License.

## Acknowledgments

This server is built on top of git-delta, an excellent diff tool that provides the syntax highlighting and formatting capabilities. It uses the Model Context Protocol specification for integration with AI assistants, and the FastMCP framework for rapid development.
