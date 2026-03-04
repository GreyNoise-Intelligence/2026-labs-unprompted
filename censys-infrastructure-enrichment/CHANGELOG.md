# Changelog

## [Unreleased] - 2026-02-07

### Added
- Timeline response parsing support in parse_censys_response.py
- `--type` parameter for explicit response type specification (host, hosts, timeline, search)
- Binary-safe mode for extract_censys_field.sh script
- Timeline parameter documentation in SKILL.md (host_id, start_time, end_time)
- Common issues & solutions section in SKILL.md
- Timeline format documentation in censys-response-format.md
- Timeline parsing examples in scripts/README.md
- Automatic null byte filtering in field extraction script

### Fixed
- parse_censys_response.py now returns structured timeline summaries (not empty array)
- Binary data in NetBIOS/other service banners no longer breaks grep operations or produces warnings
- Timeline queries now properly documented with required parameters
- Cross-platform compatibility maintained (macOS/Linux)

### Changed
- Response type auto-detection in parser (backward compatible)
- Improved error messages for unsupported response types
- Enhanced binary data handling with automatic detection and safe mode

## Technical Details

### Timeline Response Format
Timeline responses use `events[]` array structure instead of `hosts[]`:
- `events.N.resource.event_time`: ISO8601 timestamp
- `events.N.resource.service_scanned.scan.*`: Service scan details
- `events.N.resource.whois_updated`: WHOIS changes
- `events.N.resource.location_updated`: Location changes

### Parser Output Example
```json
{
  "timeline_summary": {
    "earliest_event": "2026-01-31T06:36:57Z",
    "latest_event": "2026-02-07T02:25:09Z",
    "total_events": 100,
    "observation_days": 6.83,
    "services": {
      "111/tcp/PORTMAP": {
        "port": "111",
        "protocol": "PORTMAP",
        "transport_protocol": "tcp",
        "first_seen": "2026-01-31T11:58:10Z",
        "last_seen": "2026-02-07T02:25:09Z",
        "scan_count": 16
      }
    },
    "event_types": ["service_scanned", "location_updated", "endpoint_scanned"]
  }
}
```

## Testing
Fixes tested with 403KB timeline response (7 days, 193.24.123.42):
- ✅ Timeline parsing produces structured output
- ✅ Binary data handled without errors or warnings
- ✅ Field extraction works for timeline format
- ✅ Backward compatibility maintained (hosts format still works)
- ✅ Cross-platform tested (macOS)

---

**Status**: Ready for release
