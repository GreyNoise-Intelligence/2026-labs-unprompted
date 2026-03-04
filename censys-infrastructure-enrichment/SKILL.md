---
name: censys-infrastructure-enrichment
description: Automated infrastructure enrichment using Censys internet-wide scanning data. Use when analyzing threat actor infrastructure, enriching IPs/ASNs/domains with service and software details, querying global CVE exposure, profiling network infrastructure, or retrieving historical host timelines. Triggers on requests to enrich IPs with Censys, profile infrastructure, query Censys for host details, or add infrastructure context to threat analysis.
---

# Censys Infrastructure Enrichment

Automate infrastructure profiling using Censys internet-wide scanning data. Query for detailed service, software, certificate, and vulnerability context on any internet-facing host.

## Operating Modes

This skill operates in two modes depending on invocation context:

### Full Mode (Standalone)

**When**: Analyst invokes Censys enrichment directly (e.g., "Enrich these IPs with Censys", "Profile this infrastructure").

**Requirements**:
- Create analysis directory (e.g., `analyses/YYYYMMDD-HHMMSS-censys-enrichment/`)
- Create OPERATIONS_LOG.md before any MCP calls
- Produce full enrichment report with fleet correlation analysis
- Standard output files: OPERATIONS_LOG.md, enrichment report, and data files

### Integration Mode (Background)

**When**: Launched as a subtask from a parent analysis (e.g., a campaign analysis workflow's enrichment step).

**Requirements**:
- Single markdown output file (e.g., `censys-enrichment.md`) written to the parent analysis directory
- No separate OPERATIONS_LOG.md (the parent analysis owns the log)
- No subdirectory scaffold
- Focus on fleet correlation summary for consumption by the parent report

---

## Core Workflow

### 1. Identify Targets

Determine what to enrich:

- **IPs**: Host-level infrastructure details (batch up to 50)
- **ASNs**: Network-level profiling and statistics
- **Domains**: Web property and technology analysis
- **CVEs**: Global exposure metrics
- **Certificates**: Certificate chain and issuer details

### 2. Query Censys

Select tool based on target type:

| Target | Primary Tool | Use Case |
|--------|-------------|----------|
| IPs (≤50) | `censys-platform:get_hosts` | Batch host details |
| Single IP | `censys-threat-hunting:get_host` | Deep dive |
| IP Timeline | `censys-threat-hunting:get_host_timeline` | Historical changes |
| Search query | `censys-threat-hunting:search` | Flexible queries |
| Aggregation | `censys-threat-hunting:aggregate` | Statistics |
| Domain | `censys-platform:get_web_properties` | Web technologies |
| CVE | `censys-platform:retrieve_cve_details` | Global exposure |
| Certificate | `censys-threat-hunting:get_certificate` | Cert details |
| Query help | `censys-threat-hunting:generate_query` | Natural language to CenQL |

### 3. Parse Results

Censys MCP returns responses in a flattened key-value format. For large responses (saved to file), use parsing scripts:

**Quick field extraction (bash)**:
```bash
# Extract all IPs
bash scripts/extract_censys_field.sh --file response.txt --field "hosts.*.ip"

# Extract all ports
bash scripts/extract_censys_field.sh --file response.txt --field "hosts.*.services.*.port"
```

**Structured parsing (python)**:
```bash
# Generate summary JSON (IP, ASN, location, ports)
python3 scripts/parse_censys_response.py --input response.txt --summary-only --pretty

# Full structured parsing
python3 scripts/parse_censys_response.py --input response.txt --output parsed.json
```

**Key fields to extract**:
- **Services**: port, protocol, service name, banner
- **Software**: product, version, vendor, CPE
- **Certificates**: issuer, subject, validity, SANs
- **Labels**: security classifications
- **Location**: country, city, coordinates
- **AS info**: ASN, organization name

### 4. Summarize Findings

For large responses, use the summary parser or aggregate key findings:

```bash
# Auto-generate summary
python3 scripts/parse_censys_response.py \
  --input response.txt \
  --output censys-summary.json \
  --summary-only

# Then analyze with jq
jq -r '.[].country' censys-summary.json | sort | uniq -c  # Count by country
jq -r '.[].ports[].port' censys-summary.json | sort -n | uniq  # List all ports
```

**Common aggregations**:
- Unique services across hosts
- Common software versions
- Notable security labels
- Geographic distribution

See references/censys-response-format.md for detailed format documentation.

## Common Issues & Solutions

### Issue 1: Timeline Response Too Large

**Symptoms**:
```
Error: result (XXX,XXX characters) exceeds maximum allowed tokens.
Output has been saved to /path/to/file.txt
```

**Solutions**:
1. Reduce time range to <30 days
2. Use parsing scripts immediately on saved file
3. Consider `get_host` for current snapshot instead

**Example**:
```bash
python3 scripts/parse_censys_response.py \
  --input /path/to/file.txt \
  --type timeline \
  --summary-only
```

---

### Issue 2: Empty Parsing Script Output

**Symptoms**:
```bash
python3 scripts/parse_censys_response.py --input file.txt --summary-only
# Output: []
```

**Solutions**:
1. Specify response type: `--type timeline` or `--type host`
2. Verify file format: `jq -r '.result' file.txt | head -20`
3. Update to latest parser version (must support timeline format)

---

### Issue 3: Binary Data in Responses

**Symptoms**:
```
grep: Binary file (standard input) matches
warning: command substitution: ignored null byte in input
```

**Solutions**:
1. Parsing scripts handle binary data automatically
2. For manual extraction, use: `LC_ALL=C grep ...`
3. Extract non-binary fields: `--field "*.port"` not `--field "*.banner"`

---

### Issue 4: Required Timeline Parameters

**Symptoms**:
```
Error: Input validation error: 'start_time' is a required property
```

**Solutions**:
Timeline requires three parameters:
- `host_id`: IP address
- `start_time`: ISO8601 (e.g., "2024-01-01T00:00:00Z")
- `end_time`: ISO8601 (e.g., "2026-02-07T00:00:00Z")

**Example**:
```
censys-threat-hunting:get_host_timeline
  host_id: "1.2.3.4"
  start_time: "2025-12-01T00:00:00Z"
  end_time: "2026-01-01T00:00:00Z"
```

## Tool Usage Examples

### Batch IP Enrichment

```
censys-platform:get_hosts
  ips: ["1.2.3.4", "5.6.7.8"]
```

### Single Host Details

```
censys-threat-hunting:get_host
  ip: "1.2.3.4"
```

### Search by ASN

```
censys-threat-hunting:search
  query: "autonomous_system.asn: 12345"
  per_page: 100
```

### Search by Software

```
censys-threat-hunting:search
  query: "services.software.product: nginx"
```

### Aggregate Statistics

```
censys-threat-hunting:aggregate
  query: "autonomous_system.asn: 12345"
  field: "services.port"
  number_of_buckets: 20
```

### CVE Global Exposure

```
censys-platform:retrieve_cve_details
  cve_id: "CVE-2024-12345"
```

### Host Timeline

Query historical changes for a host over time.

**Tool**: `censys-threat-hunting:get_host_timeline`

**Required Parameters**:
- `host_id`: IP address (e.g., "1.2.3.4")
- `start_time`: ISO8601 timestamp (e.g., "2024-01-01T00:00:00Z")
- `end_time`: ISO8601 timestamp (e.g., "2026-02-07T00:00:00Z")

**⚠️ WARNING**: Timeline responses can be very large (>400KB for 7 days). Recommendations:
- Limit time range to 30 days or less for initial queries
- Use parsing scripts immediately after query
- Consider `get_host` for current snapshot instead of full timeline

**Example**:
```
censys-threat-hunting:get_host_timeline
  host_id: "1.2.3.4"
  start_time: "2025-12-01T00:00:00Z"
  end_time: "2026-01-01T00:00:00Z"
```

**Parsing Large Timeline Responses**:
```bash
# Timeline data saved to file automatically if too large
timeline_file="/path/to/mcp-censys-threat-hunting-get_host_timeline-*.txt"

# Parse immediately
python3 scripts/parse_censys_response.py \
  --input "$timeline_file" \
  --type timeline \
  --summary-only \
  --pretty > timeline-summary.json

# Analyze summary
jq '.timeline_summary.services' timeline-summary.json
```

### Natural Language Query

```
censys-threat-hunting:generate_query
  prompt: "find all hosts running Apache with self-signed certificates"
```

## Response Handling

Censys responses can be large. Strategies:

1. **Auto-parse**: Use parsing scripts immediately after query for large responses
2. **Summarize**: Surface unique findings, not per-host duplication
3. **Focus**: Extract only relevant fields for the analysis
4. **Cache**: Write both raw responses and parsed summaries to files

**Recommended workflow for large responses**:
```bash
# 1. Censys query saves to file
censys_file="/path/to/mcp-censys-platform-get_hosts-*.txt"

# 2. Parse immediately
python3 scripts/parse_censys_response.py \
  --input "$censys_file" \
  --output censys-summary.json \
  --summary-only

# 3. Use parsed summary for analysis
cat censys-summary.json
```

See references/censys-response-format.md for detailed format documentation and scripts/README.md for usage examples.

## Fleet Analysis Patterns

When enriching multiple IPs from the same campaign, the key intelligence is in **cross-host correlation**, not individual host profiles. After querying all IPs, analyze for these linkage patterns:

### SSH Host Key Sharing

Shared SSH host keys across different IPs are definitive evidence of cloned infrastructure (same VM image or centralized management).

**What to look for**:
- Extract SSH ECDSA/RSA/ED25519 key fingerprints from each host
- Group IPs by shared key SHA256
- Flag any key appearing on 2+ IPs -- this is a strong infrastructure linkage indicator

**Report format**:
```markdown
**Shared SSH Host Key**: SHA256:`6c0e89c6...`
- 148.153.56.170 (Los Angeles)
- 148.153.56.174 (Los Angeles)
- 148.153.188.246 (Dallas)
→ Cloned from single image, same operator
```

### HASSH Fingerprint Correlation

Shared HASSH fingerprints indicate identical SSH client/server configurations. Less definitive than shared host keys but still a strong signal when combined with other indicators.

### Identical Service Configurations

Flag IPs sharing:
- Same software versions on same non-standard ports (e.g., nginx on port 55551)
- Identical TLS certificate subjects or issuers
- Same OS/version across hosts (e.g., all Ubuntu 18.04 with OpenSSH 7.6p1)

### Scan-Only Node Detection

IPs with zero open ports visible to Censys but known to be active sources of network traffic are dedicated scanning nodes -- purpose-built infrastructure that only initiates outbound connections. Report the ratio: "12 of 20 IPs (60%) have no open services -- scan-only nodes."

### Fleet Summary Template

After batch enrichment, produce a fleet correlation summary:

```markdown
## Infrastructure Linkage Summary

| Linkage Type | IPs Affected | Indicator |
|-------------|-------------|-----------|
| Shared SSH key | 3 IPs | SHA256:`6c0e89c6...` |
| Shared HASSH | 4 IPs | `b12d2871a1189eff...` |
| Identical services | 2 IPs | nginx:55551 + SSH:65218 |
| Zero open ports | 12 IPs | Scan-only nodes |
| Shared ASN | 5 IPs | AS4808 (UCloud) |
| Common CVEs | 8 IPs | CVE-2023-38408 (CVSS 9.8) |
```

### Summary Table Validation

**MANDATORY**: When generating summary tables with category counts and IP lists:

1. Write the IP list for each category FIRST
2. Count the IPs in each category AFTER writing them (do not pre-compute counts)
3. Verify that the count in each row matches the number of IPs actually listed in that row
4. Verify that row counts sum to the total number of IPs queried (accounting for IPs that may appear in multiple categories)
5. If an IP belongs to multiple categories, note the overlap explicitly: "N IPs total (M appear in multiple categories)"

**Common error**: Pre-computing counts from one data pass, then listing IPs from a different pass, resulting in count/list mismatches (e.g., "9 IPs with zero services" header but 15 IPs listed underneath).

---

## References

### Parsing Tools
- **scripts/parse_censys_response.py**: Python parser for flattened format → JSON
- **scripts/extract_censys_field.sh**: Bash script for quick field extraction
- **scripts/README.md**: Detailed usage guide for parsing scripts

### Documentation
- **references/censys-response-format.md**: **[CRITICAL]** Flattened format documentation with examples
- **references/censys-query-patterns.md**: Common CenQL query examples
- **references/infrastructure-patterns.md**: Infrastructure classification patterns
- **references/response-parsing-guide.md**: General response handling strategies
- **references/report-integration-template.md**: Report section templates
- **references/operations-logging-format.md**: Operations log format