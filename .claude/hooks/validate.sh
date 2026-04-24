#!/usr/bin/env bash
# Läuft vor jedem Write/Edit — blockiert wenn hardcodierte Credentials gefunden werden.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // ""')
CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // .tool_input.new_string // ""')

if [ -z "$CONTENT" ]; then
  exit 0
fi

# Bekannte Credentials und Muster die niemals im Code stehen dürfen
PATTERNS=(
  "olistPipeline[0-9]"
  "AKIA[0-9A-Z]{16}"
  "password\s*=\s*['\"][^'\"]{6,}"
  "secret\s*=\s*['\"][^'\"]{6,}"
)

for PATTERN in "${PATTERNS[@]}"; do
  if echo "$CONTENT" | grep -qiE "$PATTERN"; then
    echo "{\"decision\": \"block\", \"reason\": \"Hardcodierte Credentials gefunden in $FILE_PATH — verwende os.environ['KEY'] stattdessen.\"}"
    exit 0
  fi
done

exit 0
