# Censys MCP Flattened Response Format

**Purpose**: Reference guide for parsing Censys MCP's non-standard flattened key-value response format

**Status**: Production reference (tested with real session data)

---

## Overview

Censys MCP returns search results in a **flattened key-value format**, not standard JSON. This format uses hierarchical key paths with colons separating keys from values.

**Critical**: Standard JSON parsers (jq, JSON.parse, json.loads on the result string) will **NOT work** with this format.

---

## Response Structure

### JSON Container Format

```json
{
  "result": "hosts.0.autonomous_system.asn:152194\nhosts.0.autonomous_system.bgp_prefix:134.122.136.0/24\nhosts.0.ip:134.122.136.119\nhosts.1.ip:134.122.136.96\n..."
}
```

The `result` field contains a **newline-delimited string** of key-value pairs, not a JSON object.

---

## Key Path Structure

### Hierarchical Format

```
hosts.N.field.subfield:value
```

**Components**:
- `hosts` - Root array
- `N` - Zero-based array index (0, 1, 2, ...)
- `field.subfield` - Nested object hierarchy
- `:` - Separator between key path and value
- `value` - String representation of value

### Examples

```
hosts.0.ip:134.122.136.119
hosts.0.autonomous_system.asn:152194
hosts.0.autonomous_system.name:SHOPIFY-AS
hosts.0.location.country:Hong Kong
hosts.0.location.city:Tung Chung
hosts.0.services.0.port:22
hosts.0.services.0.service_name:SSH
hosts.0.services.1.port:443
hosts.0.services.1.service_name:HTTP
```

---

## Nested Objects

Nested objects use dot notation in the key path:

```
hosts.0.autonomous_system.asn:152194
hosts.0.autonomous_system.name:SHOPIFY-AS
hosts.0.autonomous_system.bgp_prefix:134.122.136.0/24
hosts.0.autonomous_system.country_code:HK
```

**Reconstructed Structure**:
```json
{
  "autonomous_system": {
    "asn": 152194,
    "name": "SHOPIFY-AS",
    "bgp_prefix": "134.122.136.0/24",
    "country_code": "HK"
  }
}
```

---

## Arrays

Arrays are represented with numeric indices in the key path:

```
hosts.0.services.0.port:22
hosts.0.services.0.service_name:SSH
hosts.0.services.1.port:443
hosts.0.services.1.service_name:HTTP
hosts.0.services.2.port:80
hosts.0.services.2.service_name:HTTP
```

**Reconstructed Structure**:
```json
{
  "services": [
    {"port": 22, "service_name": "SSH"},
    {"port": 443, "service_name": "HTTP"},
    {"port": 80, "service_name": "HTTP"}
  ]
}
```

---

## Common Field Paths

### Host-Level Fields

```
hosts.N.ip                                    # IP address
hosts.N.autonomous_system.asn                 # ASN number
hosts.N.autonomous_system.name                # ASN organization name
hosts.N.autonomous_system.bgp_prefix          # BGP prefix
hosts.N.autonomous_system.country_code        # ASN country
hosts.N.location.country                      # Geolocated country
hosts.N.location.city                         # Geolocated city
hosts.N.location.coordinates.latitude         # Latitude
hosts.N.location.coordinates.longitude        # Longitude
```

### Service Fields (Array)

```
hosts.N.services.M.port                       # Port number
hosts.N.services.M.service_name               # Service type (HTTP, SSH, etc.)
hosts.N.services.M.transport_protocol         # TCP/UDP
hosts.N.services.M.software.0.product         # Software product name
hosts.N.services.M.software.0.version         # Software version
hosts.N.services.M.software.0.vendor          # Software vendor
```

### Certificate Fields (Array)

```
hosts.N.services.M.tls.certificates.0.fingerprint  # Cert fingerprint
hosts.N.services.M.tls.certificates.0.issuer       # Issuer DN
hosts.N.services.M.tls.certificates.0.subject      # Subject DN
```

---

## Parsing Patterns

### ❌ What DOES NOT Work

#### 1. jq Direct Parse

```bash
jq '.result' response.txt
# ❌ Error: Invalid numeric literal at line 1, column 30
```

**Why**: The `result` field is a string, not JSON. jq can extract the string but cannot parse its contents.

#### 2. Python json.loads() on Result

```python
import json
with open('response.txt') as f:
    data = json.load(f)
parsed = json.loads(data['result'])
# ❌ json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Why**: The result string is key-value pairs, not JSON format.

#### 3. Standard JSON Path Tools

```bash
jq -r '.result | fromjson' response.txt
# ❌ Error: Invalid JSON
```

**Why**: Same issue - not valid JSON syntax.

---

### ✅ Tested Parsing Patterns

#### 1. Python: Line-by-Line Split

**Script**: `scripts/parse_censys_response.py`

```python
import json

with open('response.txt') as f:
    data = json.load(f)

result_string = data['result']
parsed = {}

for line in result_string.strip().split('\n'):
    if ':' not in line:
        continue
    key_path, value = line.split(':', 1)  # Split on first colon only
    # Build nested structure from key_path
    # (See parse_censys_response.py for full implementation)
```

**Performance**: ~0.2s for 379KB file (10 hosts)

#### 2. Bash: grep + cut Extraction

**Script**: `scripts/extract_censys_field.sh`

```bash
# Extract all IPs
grep -E "^hosts\.[0-9]+\.ip:" response_result.txt | cut -d: -f2

# Extract all ports
grep -E "^hosts\.[0-9]+\.services\.[0-9]+\.port:" response_result.txt | cut -d: -f2

# Extract ASNs
grep -E "^hosts\.[0-9]+\.autonomous_system\.asn:" response_result.txt | cut -d: -f2
```

**Performance**: ~0.01s for 379KB file

#### 3. One-Liner Field Extraction

```bash
# Extract unique countries
grep "\.location\.country:" response.txt | cut -d: -f2 | sort -u

# Count services by port
grep "\.services\.[0-9]*\.port:" response.txt | cut -d: -f2 | sort | uniq -c
```

---

## Real-World Example

### Input (Censys MCP Response)

```json
{
  "result": "hosts.0.ip:134.122.136.119\nhosts.0.autonomous_system.asn:152194\nhosts.0.autonomous_system.name:SHOPIFY-AS\nhosts.0.location.country:Hong Kong\nhosts.0.location.city:Tung Chung\nhosts.0.services.0.port:22\nhosts.0.services.0.service_name:SSH\nhosts.0.services.1.port:443\nhosts.0.services.1.service_name:HTTP\nhosts.1.ip:134.122.136.96\nhosts.1.autonomous_system.asn:152194\nhosts.1.location.country:Hong Kong\n..."
}
```

### Output (Parsed Summary)

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
  },
  {
    "ip": "134.122.136.96",
    "asn": 152194,
    "country": "Hong Kong",
    "ports": []
  }
]
```

---

## Common Parsing Errors

### Error: "Invalid numeric literal"

```
jq: error: Invalid numeric literal at line 1, column 30
```

**Cause**: Attempting to use jq to parse the flattened format as JSON

**Solution**: Use Python script or bash grep patterns instead

---

### Error: "Expecting value: line 1 column 1"

```python
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Cause**: Attempting json.loads() on the result string

**Solution**: Parse line-by-line with split(':', 1)

---

### Error: "No such file or directory"

**Cause**: Censys MCP saved large response to file, but using wrong file path

**Solution**: Check MCP tool result for file path:
```
Tool result saved to: /path/to/mcp-censys-platform-get_hosts-TIMESTAMP.txt
```

---

### Error: Null bytes in response

```
Warning: null byte(s) ignored
```

**Cause**: Censys response may contain null bytes in certain fields

**Solution**: Non-critical warning - parser handles this automatically

---

## Field Extraction Cheat Sheet

### Quick Extraction Commands

```bash
# All IPs
grep "hosts\.[0-9]*\.ip:" response.txt | cut -d: -f2

# All ASNs (with counts)
grep "autonomous_system\.asn:" response.txt | cut -d: -f2 | sort | uniq -c

# All countries (unique)
grep "location\.country:" response.txt | cut -d: -f2 | sort -u

# All open ports
grep "services\.[0-9]*\.port:" response.txt | cut -d: -f2 | sort -n | uniq

# All service names
grep "services\.[0-9]*\.service_name:" response.txt | cut -d: -f2 | sort | uniq -c

# SSL/TLS certificate fingerprints
grep "certificates\.[0-9]*\.fingerprint:" response.txt | cut -d: -f2
```

---

## Integration with Threat Hunting

### Recommended Workflow

```bash
# 1. Censys query returns large response
censys_file="/path/to/mcp-censys-platform-get_hosts-*.txt"

# 2. Parse to structured JSON
python3 scripts/parse_censys_response.py \
  --input "$censys_file" \
  --output censys-parsed.json \
  --pretty

# 3. Generate summary for reporting
python3 scripts/parse_censys_response.py \
  --input "$censys_file" \
  --summary-only \
  --output censys-summary.json

# 4. Quick field extraction for analysis
bash scripts/extract_censys_field.sh \
  --file "$censys_file" \
  --field "hosts.*.ip" > ip-list.txt
```

---

## Performance Considerations

### File Sizes

- 10 hosts: ~380KB response
- 50 hosts: ~1.9MB response
- 100 hosts: ~3.8MB response

### Parsing Speed

- Python full parse: 0.2s per 10 hosts
- Bash field extraction: 0.01s per 10 hosts
- Memory usage: ~2x response file size

### Recommendations

- Use bash extraction for quick field lookups
- Use Python parser for structured analysis
- Cache parsed results alongside raw responses
- For very large responses (>100 hosts), parse in batches

---

## Troubleshooting

### Issue: Empty Output

**Check**:
1. Verify file contains `"result":` field: `grep '"result"' file.txt`
2. Check for malformed JSON: `jq empty file.txt`
3. Verify newlines in result: `jq -r '.result' file.txt | head`

### Issue: Missing Fields

**Cause**: Not all hosts have all fields (e.g., some have no services)

**Solution**: Parser handles missing fields gracefully (returns null/empty array)

### Issue: Incorrect Array Indices

**Cause**: Manual index specification in field path doesn't match data

**Solution**: Use wildcard patterns (`hosts.*.field`) instead of specific indices

---

## Timeline Response Format

**Tool**: `censys-threat-hunting:get_host_timeline`

**Key Difference**: Timeline uses `events[]` array instead of `hosts[]` array

### Schema

```
events.N.extensions: {}
events.N.resource.event_time: ISO8601 timestamp
events.N.resource.service_scanned.scan.ip: string
events.N.resource.service_scanned.scan.port: int
events.N.resource.service_scanned.scan.protocol: string
events.N.resource.service_scanned.scan.transport_protocol: tcp|udp
events.N.resource.service_scanned.scan.banner: string (may contain binary)
events.N.resource.service_scanned.scan.banner_hash_sha256: string
events.N.resource.service_scanned.scan.scan_time: ISO8601
events.N.resource.service_scanned.scan.is_success: boolean
events.N.resource.service_scanned.diff: object|null
events.N.resource.whois_updated: object|null
events.N.resource.location_updated: object|null
events.N.resource.route_updated: object|null
```

### Example

```
events.0.resource.event_time:2026-02-07T02:25:09Z
events.0.resource.service_scanned.scan.ip:193.24.123.42
events.0.resource.service_scanned.scan.port:111
events.0.resource.service_scanned.scan.protocol:PORTMAP
events.0.resource.service_scanned.scan.transport_protocol:tcp
events.0.resource.service_scanned.scan.scan_time:2026-02-07T02:25:09Z
events.1.resource.event_time:2026-02-06T22:26:14Z
events.1.resource.service_scanned.scan.port:111
...
```

### Parsing Timeline Format

**Use timeline-specific parser**:

```bash
python3 scripts/parse_censys_response.py \
  --input timeline.json \
  --type timeline \
  --summary-only \
  --pretty
```

**Output structure**:

```json
{
  "timeline_summary": {
    "earliest_event": "2026-01-31T06:36:57Z",
    "latest_event": "2026-02-07T02:25:09Z",
    "total_events": 150,
    "observation_days": 6.82,
    "services": {
      "111/tcp/PORTMAP": {
        "port": 111,
        "protocol": "PORTMAP",
        "transport_protocol": "tcp",
        "first_seen": "2026-01-31T06:36:57Z",
        "last_seen": "2026-02-07T02:25:09Z",
        "scan_count": 45
      }
    },
    "event_types": ["service_scanned"]
  }
}
```

### Field Extraction

**Extract ports from timeline**:

```bash
bash scripts/extract_censys_field.sh \
  --file timeline.json \
  --field "events.*.resource.service_scanned.scan.port"
```

**Extract protocols**:

```bash
bash scripts/extract_censys_field.sh \
  --file timeline.json \
  --field "events.*.resource.service_scanned.scan.protocol"
```

---

## See Also

- **Scripts**: `scripts/parse_censys_response.py`, `scripts/extract_censys_field.sh`
- **Documentation**: `scripts/README.md` (usage examples)
- **Testing**: `TEST_RESULTS.md` (validation against real data)


---

**Last Updated**: 2026-02-07
**Tested With**: Censys MCP v2.x
