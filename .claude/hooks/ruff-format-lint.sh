#!/bin/bash
# PostToolUse hook: Auto-format and lint Python files after Write/Edit
set -e

# Read JSON input from stdin
input=$(cat)

# Extract file path using jq
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# Skip if no file path or not a Python file
if [[ -z "$file_path" ]] || [[ ! "$file_path" =~ \.py$ ]]; then
    exit 0
fi

# Skip if file doesn't exist
if [[ ! -f "$file_path" ]]; then
    exit 0
fi

# Run ruff format and check with auto-fix
if command -v ruff &> /dev/null; then
    ruff format "$file_path" --quiet 2>/dev/null || true
    ruff check "$file_path" --fix --quiet 2>/dev/null || true
elif command -v uv &> /dev/null; then
    uv run ruff format "$file_path" --quiet 2>/dev/null || true
    uv run ruff check "$file_path" --fix --quiet 2>/dev/null || true
fi

exit 0
