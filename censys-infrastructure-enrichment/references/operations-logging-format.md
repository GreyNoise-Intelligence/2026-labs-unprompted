# Operations Logging Format

## Standard Entry

```markdown
## Operation [N]: Censys Infrastructure Enrichment

**Timestamp**: [YYYY-MM-DDTHH:MM:SSZ]
**Tool**: [MCP tool name]
**Parameters**:
- [Parameter]: [Value]
**Results Summary**:
- [Key metric]: [Value]
**Cache File**: [Path or N/A]
**Report Update**: [Section added/modified]
```

## Tool-Specific Formats

### get_hosts (Batch IP)

```markdown
## Operation N: Censys Infrastructure Enrichment

**Timestamp**: 2026-02-03T14:30:00Z
**Tool**: censys-platform:get_hosts
**Parameters**:
- IPs: 10 (185.177.72.23, 185.177.72.13, ...)
- Fields: ip, autonomous_system.*, services.port, services.protocol, services.software.*, services.labels, operating_system.*
**Results Summary**:
- Hosts returned: 10
- Common services: SSH (10), HTTP (8), Kubelet (10)
- Infrastructure: Kubernetes cluster detected
- OS: Debian 12 (all hosts)
**Cache File**: cache/censys_hosts_20260203_143000.json
**Report Update**: Added "Infrastructure Architecture Analysis (Censys)" section
```

### get_host (Single IP)

```markdown
## Operation N: Censys Host Detail

**Timestamp**: 2026-02-03T14:35:00Z
**Tool**: censys-threat-hunting:get_host
**Parameters**:
- IP: 185.177.72.23
**Results Summary**:
- Services: 12 open ports
- Notable: Kubelet API (10250), Envoy (9964)
- Last updated: 2026-02-01
**Cache File**: N/A
**Report Update**: Enhanced host detail in infrastructure section
```

### search (ASN/Query)

```markdown
## Operation N: Censys ASN Search

**Timestamp**: 2026-02-03T14:40:00Z
**Tool**: censys-threat-hunting:search
**Parameters**:
- Query: autonomous_system.asn: 211590
- Per page: 100
**Results Summary**:
- Total hosts: 1,247
- Top ports: 22 (98%), 80 (45%), 443 (42%)
- Campaign IPs: 375 (30% of ASN)
**Cache File**: cache/censys_asn211590_20260203.json
**Report Update**: Added "Network Profile" section
```

### retrieve_cve_details

```markdown
## Operation N: Censys CVE Exposure

**Timestamp**: 2026-02-03T14:45:00Z
**Tool**: censys-platform:retrieve_cve_details
**Parameters**:
- CVE: CVE-2026-21858
**Results Summary**:
- Global exposure: 45,230 hosts
- Top affected software: Example Product 2.x
- Geographic concentration: US (35%), CN (22%)
**Cache File**: N/A
**Report Update**: Added "Global CVE Exposure" section
```

### get_host_timeline

```markdown
## Operation N: Censys Host Timeline

**Timestamp**: 2026-02-03T14:50:00Z
**Tool**: censys-threat-hunting:get_host_timeline
**Parameters**:
- IP: 185.177.72.23
**Results Summary**:
- Timeline span: 2025-08-01 to 2026-02-03
- Changes detected: 3
- Notable: Kubernetes services appeared 2025-12-15
**Cache File**: N/A
**Report Update**: Added timeline context to infrastructure section
```

## Sequence Numbering

Continue operation numbering from existing OPERATIONS_LOG.md. If previous operation was #7, next Censys operation is #8.

## Error Logging

When errors occur:

```markdown
## Operation N: Censys Infrastructure Enrichment (PARTIAL)

**Timestamp**: 2026-02-03T15:00:00Z
**Tool**: censys-platform:get_hosts
**Parameters**:
- IPs: 50 requested
**Error**: 429 Rate Limit after 20 hosts
**Results Summary**:
- Hosts returned: 20/50
- Enrichment: Partial (40%)
**Mitigation**: Cached first 20 hosts, will retry remaining in 60 minutes
**Report Update**: Added partial infrastructure section with caveat
```
