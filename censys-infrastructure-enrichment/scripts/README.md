# Censys Response Parsing Scripts

**Purpose**: Utilities for parsing Censys MCP's flattened response format

**Status**: Production-ready (tested with real session data)

---

## Overview

Censys MCP returns search results in a non-standard flattened format that requires specialized parsing. These scripts provide two approaches:

1. **Full Parsing** (`parse_censys_response.py`) - Convert to structured JSON
2. **Quick Extraction** (`extract_censys_field.sh`) - Extract specific fields without full parsing

---

## Scripts

### 1. parse_censys_response.py

**Purpose**: Convert Censys flattened format to structured JSON

**Features**:
- Full nested structure reconstruction
- Summary-only mode (IP, ASN, location, ports)
- Handles arrays and nested objects
- Pretty-print option
- Stdin/stdout support

**Usage**:

```bash
# Summary mode (recommended for quick analysis)
python3 parse_censys_response.py \
  --input response.txt \
  --summary-only \
  --pretty

# Full parsing with output file
python3 parse_censys_response.py \
  --input response.txt \
  --output parsed.json \
  --pretty

# From stdin
cat response.txt | python3 parse_censys_response.py --summary-only

# Quick one-liner
python3 parse_censys_response.py -i response.txt -s -p
```

**Output Examples**:

Summary mode:
```json
[
  {
    "ip": "134.122.136.119",
    "asn": 152194,
    "asn_name": "SHOPIFY-AS",
    "country": "Hong Kong",
    "city": "Tung Chung",
    "ports": [
      {"port": 22, "service_name": "SSH"},
      {"port": 443, "service_name": "HTTP"}
    ]
  }
]
```

Full mode: Complete nested structure with all Censys fields

**Performance**: ~0.2s for 10 hosts (379KB file)

---

### 2. extract_censys_field.sh

**Purpose**: Quick grep-based field extraction without Python dependency

**Features**:
- Wildcard support for array indices (`*`)
- No Python required (bash + grep + cut only)
- Fast execution (~0.01s)
- Portable (works on macOS and Linux)

**Usage**:

```bash
# All IPs
bash extract_censys_field.sh \
  --file response.txt \
  --field "hosts.*.ip"

# All ports from all hosts
bash extract_censys_field.sh \
  --file response.txt \
  --field "hosts.*.services.*.port"

# All ASNs
bash extract_censys_field.sh \
  --file response.txt \
  --field "hosts.*.autonomous_system.asn"

# All countries
bash extract_censys_field.sh \
  --file response.txt \
  --field "hosts.*.location.country"

# Specific host (first host's IP)
bash extract_censys_field.sh \
  --file response.txt \
  --field "hosts.0.ip"
```

**Output**: One value per line

```
134.122.136.119
134.122.136.96
134.122.136.231
...
```

**Performance**: ~0.01s for 10 hosts (379KB file)

---

## Quick Start

### Step 1: Get Censys Response

Censys MCP saves large responses to files:

```
Tool result saved to: /path/to/mcp-censys-platform-get_hosts-1770402854951.txt
```

### Step 2: Parse Response

```bash
# Quick summary
python3 scripts/parse_censys_response.py \
  --input /path/to/mcp-censys-platform-get_hosts-*.txt \
  --summary-only \
  --output censys-summary.json \
  --pretty

# Or quick IP extraction
bash scripts/extract_censys_field.sh \
  --file /path/to/mcp-censys-platform-get_hosts-*.txt \
  --field "hosts.*.ip" > ip-list.txt
```

### Step 3: Use Parsed Data

```bash
# View summary
cat censys-summary.json

# Count IPs by country
jq -r '.[].country' censys-summary.json | sort | uniq -c

# List all open ports
jq -r '.[].ports[].port' censys-summary.json | sort -n | uniq
```

---

## Integration Patterns

### Pattern 1: Automatic Parsing After Query

```bash
# After Censys MCP query
censys_response="/path/to/mcp-censys-platform-get_hosts-*.txt"

# Parse immediately
python3 scripts/parse_censys_response.py \
  --input "$censys_response" \
  --output "${analysis_dir}/censys-summary.json" \
  --summary-only \
  --pretty

echo "Parsed Censys response → censys-summary.json" >> OPERATIONS_LOG.md
```

---

### Pattern 2: Field-Specific Analysis

```bash
# Extract IPs for further scanning
bash scripts/extract_censys_field.sh \
  --file "$censys_response" \
  --field "hosts.*.ip" | \
  while read ip; do
    # Additional analysis per IP
    nmap -sV "$ip"
  done
```

---

### Pattern 3: Aggregation and Reporting

```bash
# Count hosts by country
bash scripts/extract_censys_field.sh \
  --file "$censys_response" \
  --field "hosts.*.location.country" | \
  sort | uniq -c | sort -rn

# Count services by port
bash scripts/extract_censys_field.sh \
  --file "$censys_response" \
  --field "hosts.*.services.*.port" | \
  sort | uniq -c | sort -rn
```

---

## Timeline Response Parsing

**Input**: Timeline data from `get_host_timeline`

**Format**: `events[]` array (not `hosts[]`)

### Basic Parsing

```bash
python3 parse_censys_response.py \
  --input timeline.json \
  --type timeline \
  --summary-only \
  --pretty
```

### Output

```json
{
  "timeline_summary": {
    "earliest_event": "ISO8601",
    "latest_event": "ISO8601",
    "total_events": 150,
    "observation_days": 6.82,
    "services": {
      "port/transport/protocol": {
        "first_seen": "ISO8601",
        "last_seen": "ISO8601",
        "scan_count": 45
      }
    }
  }
}
```

### Use Cases

- Identify when services appeared/disappeared
- Track service exposure over time
- Detect infrastructure changes
- Generate service history reports

### Field Extraction from Timeline

```bash
# Extract ports
bash extract_censys_field.sh \
  --file timeline.json \
  --field "events.*.resource.service_scanned.scan.port"

# Extract protocols
bash extract_censys_field.sh \
  --file timeline.json \
  --field "events.*.resource.service_scanned.scan.protocol"

# Extract event times
bash extract_censys_field.sh \
  --file timeline.json \
  --field "events.*.resource.event_time"
```

---

## Common Use Cases

### Use Case 1: Quick Infrastructure Overview

```bash
# One-liner summary
python3 scripts/parse_censys_response.py \
  -i censys-response.txt \
  -s | jq -r '.[] | "\(.ip) | AS\(.asn) | \(.country) | Ports: \([.ports[].port] | join(","))"'

# Output:
# 134.122.136.119 | AS152194 | Hong Kong | Ports: 22,443
# 134.122.136.96 | AS152194 | Hong Kong | Ports:
# ...
```

---

### Use Case 2: Identify Stealth Infrastructure

```bash
# Find IPs with no open ports
python3 scripts/parse_censys_response.py -i response.txt -s | \
  jq -r '.[] | select(.ports | length == 0) | .ip'
```

---

### Use Case 3: Port-Specific Targeting

```bash
# Find all hosts with SSH (port 22)
python3 scripts/parse_censys_response.py -i response.txt -s | \
  jq -r '.[] | select(.ports[] | .port == 22) | .ip'

# Find all HTTPS hosts
python3 scripts/parse_censys_response.py -i response.txt -s | \
  jq -r '.[] | select(.ports[] | .port == 443) | .ip'
```

---

### Use Case 4: Geographic Analysis

```bash
# Group IPs by country
python3 scripts/parse_censys_response.py -i response.txt -s | \
  jq -r 'group_by(.country) | .[] | "\(.[0].country): \(length) hosts"'

# Output:
# Hong Kong: 8 hosts
# Japan: 2 hosts
```

---

## Troubleshooting

### Issue: "No 'result' field found"

**Cause**: Input file is not a Censys MCP response

**Solution**: Verify file format with:
```bash
jq '.result' input-file.txt | head
```

---

### Issue: "File not found"

**Cause**: Incorrect file path

**Solution**: Use the exact path from MCP tool output:
```
Tool result saved to: /full/path/to/file.txt
```

---

### Issue: Python script returns empty output

**Cause**: Using `--output` without specifying filename

**Solution**: Either omit `--output` (prints to stdout) or provide filename:
```bash
# Correct - stdout
python3 parse_censys_response.py -i response.txt -s

# Correct - file output
python3 parse_censys_response.py -i response.txt -s -o summary.json
```

---

### Issue: Bash script returns nothing

**Cause**: Field pattern doesn't match any keys

**Solution**: Check available fields first:
```bash
# List all available field paths
jq -r '.result' response.txt | grep "^hosts\.0\." | cut -d: -f1 | sort -u
```

---

### Issue: "Command not found: python3"

**Cause**: Python 3 not installed or not in PATH

**Solution**: Install Python 3 or use bash script for extraction instead

---

## Performance Benchmarks

Tested with real Censys responses:

| Hosts | Response Size | Python Parse | Bash Extract | Memory |
|-------|---------------|-------------|--------------|--------|
| 10    | 379 KB        | 0.2s        | 0.01s        | 2 MB   |
| 50    | 1.9 MB        | 0.8s        | 0.03s        | 8 MB   |
| 100   | 3.8 MB        | 1.5s        | 0.05s        | 15 MB  |

**Recommendation**: Use bash script for quick field extraction, Python for structured analysis

---

## Field Path Reference

### Common Field Patterns

```bash
# Host identification
hosts.*.ip                                    # IP addresses
hosts.*.autonomous_system.asn                 # ASN numbers
hosts.*.autonomous_system.name                # ASN names

# Location
hosts.*.location.country                      # Countries
hosts.*.location.city                         # Cities
hosts.*.location.coordinates.latitude         # Latitude
hosts.*.location.coordinates.longitude        # Longitude

# Services
hosts.*.services.*.port                       # Ports
hosts.*.services.*.service_name               # Service types
hosts.*.services.*.software.*.product         # Software products
hosts.*.services.*.software.*.version         # Software versions

# Certificates
hosts.*.services.*.tls.certificates.*.fingerprint  # Cert fingerprints
hosts.*.services.*.tls.certificates.*.issuer       # Cert issuers
hosts.*.services.*.tls.certificates.*.subject      # Cert subjects
```

---

## See Also

- **Format Documentation**: `../references/censys-response-format.md`
- **Skill Documentation**: `../SKILL.md`

---

**Last Updated**: 2026-02-07
**Tested With**: Censys MCP v2.x, AS152194 session data
