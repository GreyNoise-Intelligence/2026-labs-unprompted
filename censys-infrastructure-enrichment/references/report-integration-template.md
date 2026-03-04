# Report Integration Templates

> **Note**: These are section templates meant to be embedded in parent reports. If a Censys enrichment report is produced as a standalone artifact, prepend the following after any metadata header:
>
> ```markdown
> > **AI-Assisted Analysis**: This report was produced with AI-powered analytical assistance. Infrastructure assessments and correlation conclusions are LLM-generated based on real data queried from Censys and other sources. Outputs should undergo validation and review by a human analyst before distribution. Generative and speculative elements may contain errors or inaccuracies.
> ```

## Standard Infrastructure Section

```markdown
### Infrastructure Analysis (Censys)

Censys data for [N] analyzed hosts[^N]:

**Service Profile**:

| Port | Protocol | Service | Software |
|------|----------|---------|----------|
| [port] | [proto] | [svc] | [version] |

**Infrastructure**: [Cloud provider / Hosting type / VPS]

**Notable Findings**: [Key observations]
```

## Host Detail Section

```markdown
### Host Profile: [IP] (Censys)

**Location**: [City], [Country]
**ASN**: AS[number] ([Organization])
**Last Observed**: [Date]

**Services**:

| Port | Service | Software | Labels |
|------|---------|----------|--------|
| [port] | [svc] | [software] | [labels] |

**Certificates**: [Summary of TLS certs if present]
```

## ASN Profile Section

```markdown
### Network Profile: AS[NUMBER] (Censys)

**Organization**: [ASN Name]
**Total Hosts**: [Count from search]

**Top Services**:

| Port | Count | Percentage |
|------|-------|------------|
| [port] | [n] | [%] |

**Common Software**: [Top products]
```

## CVE Exposure Section

```markdown
### CVE Global Exposure (Censys)

**[CVE-ID]**: [Description]

| Metric | Value |
|--------|-------|
| Global Hosts | [N] |
| Top Countries | [List] |
| Affected Software | [Products] |
```

## Timeline Section

```markdown
### Infrastructure Timeline: [IP] (Censys)

| Date | Change |
|------|--------|
| [date] | [Description of change] |

**Analysis**: [Observations about infrastructure evolution]
```

## Footnote Format

```markdown
[^N]: Censys query, [YYYY-MM-DD]. Tool: [tool name].
```

## Operations Log Entry

```markdown
## Operation [N]: Censys Enrichment

**Timestamp**: [ISO 8601]
**Tool**: [MCP tool name]
**Query/Parameters**: [Details]
**Results**: [Summary]
```
