# Censys Response Parsing Guide

## Response Size Management

Censys responses can be large:

- Full response (10 IPs, all fields): ~335KB
- Optimized (10 IPs, essential fields): ~80KB

### Field Limiting Strategy

**Always include**:

- `ip`
- `autonomous_system.asn`
- `autonomous_system.name`
- `location.country`
- `services.port`
- `services.protocol`

**Conditionally include**:

- `services.banner` (truncate if >200 chars)
- `services.software.*`
- `services.labels`

**Exclude for size**:

- Full certificates (`services.tls.certificates.chain.*`)
- Raw HTTP bodies
- Verbose metadata fields

## Parsing get_hosts Response

The `censys-platform:get_hosts` response structure:

```json
{
  "results": [
    {
      "ip": "1.2.3.4",
      "autonomous_system": {
        "asn": 12345,
        "name": "Example AS"
      },
      "location": {
        "country": "US",
        "city": "New York"
      },
      "services": [
        {
          "port": 22,
          "protocol": "SSH",
          "banner": "SSH-2.0-OpenSSH_9.2p1",
          "software": [
            {"product": "OpenSSH", "version": "9.2p1"}
          ],
          "labels": ["ssh"]
        }
      ],
      "operating_system": {
        "product": "Debian",
        "version": "12"
      }
    }
  ]
}
```

## Summarization Strategy

For large responses, summarize to avoid context overflow:

1. **Unique services**: List each port/service once, note host count

```markdown
| Port | Service | Hosts | Software |
|------|---------|-------|----------|
| 22 | SSH | 10/10 | OpenSSH 9.2p1 |
| 80 | HTTP | 8/10 | nginx 1.22 |
```

2. **Common patterns**: Group hosts by infrastructure type

```markdown
**Pattern A** (8 hosts): Kubernetes cluster (ports 10250, 10256, 9964)
**Pattern B** (2 hosts): Standard web server (ports 22, 80, 443)
```

3. **Notable findings only**: Surface security-relevant discoveries

## Error Handling

| Error | Response | Action |
|-------|----------|--------|
| 429 Rate Limit | Use cached data | Note "cached from [date]" |
| 404 Not Found | IP not in database | Skip, note "not observed" |
| 403 Quota | Prioritize critical IPs | Note partial enrichment |
| Timeout | Retry with backoff | Max 3 retries |

## Caching Large Responses

When response exceeds 100KB:

1. Write raw JSON to cache file:

```
/path/to/analysis/cache/censys_hosts_YYYYMMDD_HHMMSS.json
```

2. Reference in operations log
3. Parse and summarize for report
4. Keep cache for 24 hours minimum
