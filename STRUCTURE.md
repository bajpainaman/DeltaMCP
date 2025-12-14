# Project Structure

This document outlines the organization of the Delta MCP server codebase.

## Core Modules

**server.py** - Main MCP server implementation. Defines all MCP tools and handles the server lifecycle. This is the entry point for the MCP server.

**delta_wrapper.py** - Handles execution of delta commands via subprocess. Provides safe execution with timeouts, size limits, and proper encoding handling. Also handles piping git output to delta.

**delta_utils.py** - Utilities for checking delta installation and version. Verifies delta is available before attempting to use it.

**config_manager.py** - Manages delta configuration by parsing Git's config files. Reads the `[delta]` section from `~/.gitconfig` and merges it with per-request overrides.

**validation.py** - Input validation and sanitization utilities. Validates file paths, commit ranges, grep tools, and programming languages to prevent security issues.

**git_utils.py** - Git repository detection utilities. Checks if the current directory is a git repository and retrieves the repository root path.

**browser_utils.py** - Browser integration utilities. Converts ANSI-colored output to HTML, creates static HTML files for browser viewing, and generates terminal hyperlinks using OSC 8 escape sequences.

**resources.py** - MCP resource definitions. Registers resources that provide direct access to formatted data without explicit tool calls.

## Configuration

**config/example.gitconfig** - Example Git configuration file showing how to configure delta with various options.

**examples/** - Example MCP client configuration files for Claude Desktop, Cursor, and Warp.

**manifest.json** - MCPB manifest for packaging the server as a one-click installable bundle.

**pyproject.toml** - Python project configuration including dependencies and build metadata.

## Tests

**tests/** - Unit and integration tests for validation, configuration management, and git utilities.

## Build Artifacts

The `.gitignore` file excludes build artifacts, cache files, virtual environments, and IDE-specific files from version control.

