#!/usr/bin/env bash
#
# Censys Flattened Format Field Extractor
#
# Quick grep-based extraction of fields from Censys MCP responses
# without requiring Python or full parsing.
#
# Usage:
#   bash extract_censys_field.sh --file response.txt --field "hosts.*.ip"
#   bash extract_censys_field.sh --file response.txt --field "hosts.0.services.*.port"
#
# Field Pattern Syntax:
#   - Use * as wildcard for array indices
#   - Examples:
#     hosts.*.ip                           -> All IP addresses
#     hosts.*.services.*.port             -> All ports from all hosts
#     hosts.0.autonomous_system.asn       -> ASN of first host
#     hosts.*.location.country            -> All countries
#
# Notes:
#   - Compatible with both macOS (BSD) and Linux (GNU) tools
#   - Uses only grep and cut for maximum portability
#   - Returns one value per line
#

set -euo pipefail

# Default values
FILE=""
FIELD=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --file|-f)
            FILE="$2"
            shift 2
            ;;
        --field|--key|-k)
            FIELD="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 --file <file> --field <field-pattern>"
            echo ""
            echo "Examples:"
            echo "  $0 --file response.txt --field 'hosts.*.ip'"
            echo "  $0 --file response.txt --field 'hosts.*.services.*.port'"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

# Validate arguments
if [[ -z "$FILE" ]]; then
    echo "Error: --file is required" >&2
    exit 1
fi

if [[ -z "$FIELD" ]]; then
    echo "Error: --field is required" >&2
    exit 1
fi

if [[ ! -f "$FILE" ]]; then
    echo "Error: File not found: $FILE" >&2
    exit 1
fi

# Extract the result field from JSON
# Try Python first (most reliable), fall back to grep if not available
# Filter null bytes from output to avoid bash warnings
if command -v python3 &> /dev/null; then
    RESULT=$(python3 -c "import json, sys; data=json.load(open('$FILE')); result = data.get('result', ''); print(result.replace('\x00', ''), end='')" 2>/dev/null)
elif command -v python &> /dev/null; then
    RESULT=$(python -c "import json, sys; data=json.load(open('$FILE')); result = data.get('result', ''); print result.replace('\x00', '')," 2>/dev/null)
else
    # Fallback: assume file is already the extracted result (not full JSON)
    # This handles pre-processed files
    if grep -q '^hosts\.' "$FILE" 2>/dev/null; then
        RESULT=$(cat "$FILE")
    else
        echo "Error: Python not found and file doesn't appear to be pre-processed result" >&2
        echo "Install Python 3 or pre-extract the result field with:" >&2
        echo "  jq -r '.result' input.json > result.txt" >&2
        exit 1
    fi
fi

if [[ -z "$RESULT" ]]; then
    echo "Error: No 'result' field found in file or empty result" >&2
    exit 1
fi

# Convert field pattern to grep pattern
# Replace * with [0-9]+ for regex matching
# Escape dots for literal matching
GREP_PATTERN="^${FIELD}:"
GREP_PATTERN="${GREP_PATTERN//\*/[0-9]+}"
GREP_PATTERN="${GREP_PATTERN//./\\.}"

# Detect binary content by checking for null bytes
HAS_BINARY=0
if echo "$RESULT" | LC_ALL=C grep -q $'\x00' 2>/dev/null; then
    HAS_BINARY=1
    echo "WARNING: Binary data detected in response, using binary-safe mode" >&2
fi

# Extract matching lines from result
# Use LC_ALL=C for binary-safe operation
# Use printf to handle escaped newlines from JSON
if [ $HAS_BINARY -eq 1 ]; then
    echo "$RESULT" | \
        sed 's/\\n/\n/g' | \
        LC_ALL=C grep -E "$GREP_PATTERN" | \
        cut -d: -f2-
else
    echo "$RESULT" | \
        sed 's/\\n/\n/g' | \
        grep -E "$GREP_PATTERN" | \
        cut -d: -f2-
fi

# Note: The cut -d: -f2- extracts everything after the first colon
# This handles values that contain colons (like URLs)
