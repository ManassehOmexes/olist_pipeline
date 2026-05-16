#!/usr/bin/env bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')

echo "$FILE_PATH" | grep -qE '\.py$' || exit 0

PYTHON=".venv/Scripts/python.exe"
if [ ! -f "$PYTHON" ]; then
    PYTHON="python"
fi

if ! "$PYTHON" -m py_compile "$FILE_PATH" 2>/dev/null; then
    echo '{"systemMessage": "Python syntax error detected - please check the file"}'
fi
