# Infrastructure Pattern Detection

## Cloud Platforms

### AWS

| Indicator | Type |
|-----------|------|
| `*.amazonaws.com` | Certificate CN |
| `ec2.internal` | DNS hostname |
| `Amazon` in cert issuer | Certificate |
| AS16509, AS14618 | ASN |

### GCP

| Indicator | Type |
|-----------|------|
| `*.googleusercontent.com` | Certificate |
| `Google Trust Services` | Cert issuer |
| AS15169 | ASN |

### Azure

| Indicator | Type |
|-----------|------|
| `*.azure.com` | Certificate CN |
| `Microsoft` in cert issuer | Certificate |
| AS8075 | ASN |

### DigitalOcean

| Indicator | Type |
|-----------|------|
| AS14061 | ASN |
| Reverse DNS pattern | `*.digitalocean.com` |

### Other VPS Providers

| Provider | ASN | Notes |
|----------|-----|-------|
| Vultr | AS20473 | Budget VPS |
| Linode | AS63949 | Now Akamai |
| OVH | AS16276 | European hosting |
| Hetzner | AS24940 | German hosting |

## Hosting Control Panels

| Ports | Product |
|-------|---------|
| 2082, 2083, 2086, 2087 | cPanel/WHM |
| 8443, 8447 | Plesk |
| 2222 | DirectAdmin |

## Common Service Signatures

### Web Servers

| Software | Banner Pattern |
|----------|---------------|
| nginx | `nginx/X.X.X` |
| Apache | `Apache/X.X.X` |
| IIS | `Microsoft-IIS/X.X` |
| LiteSpeed | `LiteSpeed` |

### SSH Servers

| Software | Banner Pattern |
|----------|---------------|
| OpenSSH | `SSH-2.0-OpenSSH_X.X` |
| Dropbear | `SSH-2.0-dropbear` |

### Mail Servers

| Software | Ports |
|----------|-------|
| Postfix | 25, 587 |
| Dovecot | 143, 993 |
| Exchange | 25, 443 |

## Security Labels

Censys applies labels to hosts. Common labels:

| Label | Meaning |
|-------|---------|
| `self-signed` | Self-signed TLS certificate |
| `expired-cert` | Expired certificate |
| `default-page` | Default web server page |
| `login-page` | Authentication interface |
| `database` | Database service exposed |

## Classification Approach

1. Check ASN against known cloud/hosting providers
2. Look for control panel ports
3. Examine certificate issuers
4. Review service banners for software signatures
5. Note security labels

Report findings with evidence (port, banner, certificate, or ASN that led to classification).
