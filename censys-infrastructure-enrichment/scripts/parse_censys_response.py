#!/usr/bin/env python3
"""
Censys Flattened Response Parser

Parses Censys MCP's flattened key-value format into structured JSON.

Format: hosts.N.field.subfield:value or events.N.field.subfield:value
Example: hosts.0.ip:134.122.136.119

Usage:
    # Full parsing
    python3 parse_censys_response.py --input response.txt --output parsed.json --pretty

    # Summary only (IP, ASN, location, ports)
    python3 parse_censys_response.py --input response.txt --summary-only

    # Timeline parsing
    python3 parse_censys_response.py --input timeline.txt --type timeline --summary-only

    # From stdin
    cat response.txt | python3 parse_censys_response.py --summary-only
"""

import json
import sys
import argparse
from collections import defaultdict
from typing import Any, Dict, List


def parse_flattened_response(result_string: str) -> Dict[str, Any]:
    """
    Parse flattened Censys response format into nested dictionary.

    Args:
        result_string: Newline-delimited key:value pairs from Censys MCP

    Returns:
        Dictionary with nested structure
    """
    parsed = {}

    for line in result_string.strip().split('\n'):
        if not line or ':' not in line:
            continue

        # Split on first colon only (values may contain colons)
        key_path, value = line.split(':', 1)

        # Handle null values
        if value == 'null' or value == '':
            value = None

        # Parse key path into parts
        parts = key_path.split('.')

        # Build nested structure
        current = parsed
        for i, part in enumerate(parts[:-1]):
            # Check if this is an array index
            if part.isdigit():
                part = int(part)
                # Ensure parent is a list
                parent_key = parts[i-1] if i > 0 else 'root'
                if not isinstance(current, list):
                    # Convert to list if needed
                    if isinstance(current, dict) and parent_key in current:
                        if not isinstance(current[parent_key], list):
                            current[parent_key] = []
                        current = current[parent_key]

                # Extend list if needed
                while len(current) <= part:
                    current.append({})
                current = current[part]
            else:
                # Dictionary key
                if part not in current:
                    # Peek ahead to see if next part is a digit
                    next_part = parts[i+1] if i+1 < len(parts) else None
                    if next_part and next_part.isdigit():
                        current[part] = []
                    else:
                        current[part] = {}
                current = current[part]

        # Set the final value
        final_key = parts[-1]
        if isinstance(current, list):
            # Handle array assignment
            idx = int(final_key)
            while len(current) <= idx:
                current.append({})
            current[idx] = value
        else:
            current[final_key] = value

    return parsed


def detect_response_type(parsed_data: Dict[str, Any], explicit_type: str = None) -> str:
    """
    Detect the type of Censys response.

    Args:
        parsed_data: Parsed nested dictionary
        explicit_type: User-provided type override

    Returns:
        'host', 'hosts', 'timeline', 'search', or 'unknown'
    """
    if explicit_type:
        return explicit_type

    # Check for timeline format
    if 'events' in parsed_data:
        return 'timeline'

    # Check for host/hosts format
    if 'hosts' in parsed_data:
        return 'hosts'

    # Check for single host format (top-level fields)
    if 'ip' in parsed_data or 'services' in parsed_data:
        return 'host'

    return 'unknown'


def extract_timeline_summary(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract summary information from parsed timeline data.

    Returns:
        Dictionary with timeline summary:
        - earliest_event: ISO8601 timestamp
        - latest_event: ISO8601 timestamp
        - total_events: int
        - observation_days: float
        - services: dict of port/protocol info
        - event_types: list of event type names
    """
    from datetime import datetime

    events = parsed_data.get('events', [])

    if not events:
        return {
            'timeline_summary': {
                'error': 'No events found in timeline data'
            }
        }

    # Initialize tracking structures
    services = {}  # Key: "port/transport/protocol", Value: service info
    event_types = set()
    timestamps = []

    for event in events:
        if not isinstance(event, dict):
            continue

        resource = event.get('resource', {})
        if not isinstance(resource, dict):
            continue

        # Track event time
        event_time = resource.get('event_time')
        if event_time:
            timestamps.append(event_time)

        # Process service_scanned events
        if 'service_scanned' in resource and resource['service_scanned']:
            event_types.add('service_scanned')
            scan_data = resource['service_scanned'].get('scan', {})

            if isinstance(scan_data, dict):
                port = scan_data.get('port')
                protocol = scan_data.get('protocol', 'UNKNOWN')
                transport = scan_data.get('transport_protocol', 'unknown')
                scan_time = scan_data.get('scan_time')

                if port:
                    # Create service key
                    service_key = f"{port}/{transport}/{protocol}"

                    if service_key not in services:
                        services[service_key] = {
                            'port': port,
                            'protocol': protocol,
                            'transport_protocol': transport,
                            'first_seen': scan_time,
                            'last_seen': scan_time,
                            'scan_count': 0
                        }

                    # Update last_seen and scan count
                    if scan_time:
                        if scan_time < services[service_key]['first_seen']:
                            services[service_key]['first_seen'] = scan_time
                        if scan_time > services[service_key]['last_seen']:
                            services[service_key]['last_seen'] = scan_time

                    services[service_key]['scan_count'] += 1

        # Track other event types
        for event_type in ['whois_updated', 'location_updated', 'route_updated',
                          'reverse_dns_resolved', 'forward_dns_resolved',
                          'jarm_scanned', 'endpoint_scanned']:
            if event_type in resource and resource[event_type]:
                event_types.add(event_type)

    # Calculate time range
    earliest = min(timestamps) if timestamps else None
    latest = max(timestamps) if timestamps else None

    observation_days = None
    if earliest and latest:
        try:
            start = datetime.fromisoformat(earliest.replace('Z', '+00:00'))
            end = datetime.fromisoformat(latest.replace('Z', '+00:00'))
            observation_days = (end - start).total_seconds() / 86400
        except:
            pass

    return {
        'timeline_summary': {
            'earliest_event': earliest,
            'latest_event': latest,
            'total_events': len(events),
            'observation_days': round(observation_days, 2) if observation_days else None,
            'services': services,
            'event_types': sorted(list(event_types))
        }
    }


def extract_summary(parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract summary information from parsed Censys data.

    Returns list of host summaries with key fields:
    - ip
    - asn
    - country
    - city
    - ports
    """
    summary = []

    hosts = parsed_data.get('hosts', [])
    for host in hosts:
        if not isinstance(host, dict):
            continue

        host_summary = {
            'ip': host.get('ip'),
            'asn': None,
            'asn_name': None,
            'country': None,
            'city': None,
            'ports': []
        }

        # Extract ASN info
        if 'autonomous_system' in host:
            asn = host['autonomous_system']
            if isinstance(asn, dict):
                host_summary['asn'] = asn.get('asn')
                host_summary['asn_name'] = asn.get('name')

        # Extract location info
        if 'location' in host:
            location = host['location']
            if isinstance(location, dict):
                host_summary['country'] = location.get('country')
                host_summary['city'] = location.get('city')

        # Extract ports
        if 'services' in host:
            services = host['services']
            if isinstance(services, list):
                for service in services:
                    if isinstance(service, dict) and 'port' in service:
                        port_info = {
                            'port': service.get('port'),
                            'service_name': service.get('service_name')
                        }
                        # Extract software info if available
                        if 'software' in service and isinstance(service['software'], list):
                            software = service['software']
                            if software and isinstance(software[0], dict):
                                port_info['product'] = software[0].get('product')
                                port_info['version'] = software[0].get('version')
                        host_summary['ports'].append(port_info)

        summary.append(host_summary)

    return summary


def main():
    parser = argparse.ArgumentParser(
        description='Parse Censys MCP flattened response format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--input', '-i',
        help='Input file path (Censys MCP response). Use - or omit for stdin'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output file path (JSON). Omit for stdout'
    )
    parser.add_argument(
        '--summary-only', '-s',
        action='store_true',
        help='Output summary only (IP, ASN, location, ports)'
    )
    parser.add_argument(
        '--pretty', '-p',
        action='store_true',
        help='Pretty-print JSON output'
    )
    parser.add_argument(
        '--type', '-t',
        choices=['host', 'hosts', 'timeline', 'search'],
        help='Response type (auto-detected if not specified)'
    )

    args = parser.parse_args()

    # Read input
    if args.input and args.input != '-':
        with open(args.input, 'r') as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    # Extract result string
    if 'result' not in data:
        print("Error: Input does not contain 'result' field", file=sys.stderr)
        sys.exit(1)

    result_string = data['result']

    # Parse flattened format
    parsed = parse_flattened_response(result_string)

    # Detect response type
    response_type = detect_response_type(parsed, args.type if hasattr(args, 'type') else None)

    # Generate summary if requested
    if args.summary_only:
        if response_type == 'timeline':
            output_data = extract_timeline_summary(parsed)
        elif response_type == 'host' or response_type == 'hosts':
            output_data = extract_summary(parsed)
        else:
            print(f"Error: Unknown response type '{response_type}'", file=sys.stderr)
            print(f"Detected keys: {list(parsed.keys())}", file=sys.stderr)
            sys.exit(1)
    else:
        output_data = parsed

    # Write output
    json_kwargs = {'indent': 2} if args.pretty else {}

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(output_data, f, **json_kwargs)
    else:
        print(json.dumps(output_data, **json_kwargs))


if __name__ == '__main__':
    main()
