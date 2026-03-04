# Censys Query Patterns (CenQL)

## Basic Queries

### By IP/CIDR

```
ip: 192.168.1.1
ip: 192.168.1.0/24
```

### By ASN

```
autonomous_system.asn: 12345
autonomous_system.name: "Example Organization"
```

### By Port

```
services.port: 22
services.port: 443 AND services.port: 80
services.port: [22, 80, 443]
```

### By Country

```
location.country_code: US
location.country_code: (US OR GB OR DE)
```

## Software Queries

### By Product

```
services.software.product: nginx
services.software.product: "Microsoft IIS"
```

### By Version

```
services.software.product: nginx AND services.software.version: 1.18*
services.software.version: 7.4*
```

### By CPE

```
services.software.cpe: "cpe:2.3:a:apache:http_server:*"
```

## Certificate Queries

### By Subject

```
services.tls.certificates.leaf_data.subject.common_name: "*.example.com"
services.tls.certificates.leaf_data.subject.organization: "Example Inc"
```

### By Issuer

```
services.tls.certificates.leaf_data.issuer.common_name: "Let's Encrypt"
services.tls.certificates.leaf_data.issuer.organization: "DigiCert"
```

### By Validity

```
services.tls.certificates.leaf_data.validity.end: [* TO 2024-01-01]
```

## Banner Queries

### Contains Text

```
services.banner: "Apache"
services.banner: "Welcome"
```

### Regex Pattern

```
services.banner: /.*admin.*/
services.banner: /SSH-2.0-.*/
```

## Label Queries

```
labels: "self-signed"
labels: "default-page"
labels: "database"
```

## Operating System

```
operating_system.product: Linux
operating_system.product: Windows AND operating_system.version: "Server 2019"
```

## Compound Queries

### Logical Operators

```
services.port: 22 AND services.port: 80
services.port: 22 OR services.port: 3389
NOT services.port: 22
```

### Grouping

```
(services.port: 80 OR services.port: 443) AND autonomous_system.asn: 12345
```

## Aggregation Fields

Common fields for `aggregate` tool:

- `services.port` - Port distribution
- `services.software.product` - Software distribution
- `services.software.vendor` - Vendor distribution
- `location.country_code` - Geographic distribution
- `autonomous_system.asn` - ASN distribution
- `labels` - Label distribution
- `operating_system.product` - OS distribution

Example:

```
query: "autonomous_system.asn: 12345"
field: "services.port"
number_of_buckets: 20
```

**⚠️ Parameter types**: `number_of_buckets` must be an integer (e.g., `20`), not a string (e.g., `"20"`).

## Tips

- Use quotes for exact phrases: `"Microsoft IIS"`
- Use wildcards for partial matches: `nginx*`, `1.18*`
- Use brackets for lists: `[22, 80, 443]`
- Use parentheses for grouping: `(A OR B) AND C`
- Field names are case-sensitive
