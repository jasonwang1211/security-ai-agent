# v1.1 Log Ingestion

## Purpose

v1.1 Log Ingestion adds a standalone pipeline for turning raw security log files into structured events that can be reviewed, demonstrated, and later integrated into the main `SecurityAgent` workflow.

The feature is intentionally lightweight. It focuses on deterministic parsing and normalization before any LLM or response logic is involved.

## Pipeline

```text
Raw Log File
    |
    v
Log Parser
    |
    v
Event Normalizer
    |
    v
Event Aggregator
    |
    v
Aggregated Events
```

### Components

| Component | File | Responsibility |
|---|---|---|
| Log Parser | `modules/log_parser.py` | Converts a raw log line into a parsed dictionary. |
| Event Normalizer | `modules/event_normalizer.py` | Converts parsed logs into normalized event records. |
| Event Aggregator | `modules/event_aggregator.py` | Detects higher-level patterns such as brute-force candidates. |
| Demo Script | `demo_log_ingestion.py` | Runs the full pipeline against a log file and prints JSON output. |

## Supported Log Formats

### Key-Value Log

```text
timestamp=2026-04-28T10:00:01Z src_ip=192.168.1.10 event=login_failed user=admin endpoint=/login status=401
```

### Simple Auth Log

```text
2026-04-28T10:00:01Z login_failed src_ip=192.168.1.10 user=admin endpoint=/login
```

### Web Access Log

```text
192.168.1.20 - - [28/Apr/2026:10:00:01 +0800] "GET /search?q=<script>alert(1)</script> HTTP/1.1" 200
```

The web access parser supports suspicious request targets that contain spaces, such as SQL injection-style query strings:

```text
192.168.1.21 - - [28/Apr/2026:10:05:14 +0800] "GET /products?id=1' or '1'='1 HTTP/1.1" 200
```

## Demo Files

| File | Purpose |
|---|---|
| `demo_logs/auth_bruteforce.log` | Contains repeated failed login events from the same source IP against `/login`. |
| `demo_logs/web_attack.log` | Contains suspicious web requests with XSS, SQL Injection, and Path Traversal payloads. |
| `demo_logs/normal_access.log` | Contains normal successful web requests and a normal login success event. |

## Running the Demo

```bash
python demo_log_ingestion.py demo_logs/auth_bruteforce.log
python demo_log_ingestion.py demo_logs/web_attack.log
python demo_log_ingestion.py demo_logs/normal_access.log
```

The script prints three JSON sections:

```text
Parsed Logs
Normalized Events
Aggregated Events
```

## Expected Results

### `demo_logs/auth_bruteforce.log`

Expected to produce one aggregated event:

```json
{
  "event_type": "brute_force_candidate",
  "source_ip": "192.168.1.10",
  "target": "/login",
  "failed_count": 10
}
```

### `demo_logs/web_attack.log`

Expected to preserve suspicious payloads in normalized web request events:

- XSS payload from the `q` query parameter.
- SQL Injection payload containing `or '1'='1`.
- Path Traversal payload containing `../../etc/passwd`.

These events remain `web_request` events in the aggregated output.

### `demo_logs/normal_access.log`

Expected to preserve normal `web_request` events and not produce a `brute_force_candidate`.

## Current Limitations

- The parser supports only the three v1.1 demo log formats.
- Timestamps are preserved as strings and are not normalized into a single datetime format.
- Brute-force aggregation is count-based only and does not use a time window yet.
- Web access parsing expects a quoted request section with an HTTP version.
- The ingestion layer does not currently enrich events with geolocation, asset identity, severity, or MITRE ATT&CK mapping.
- The demo script prints results to stdout and does not persist them.

## Future Integration Plan with `SecurityAgent`

The v1.1 ingestion layer is designed to become a preprocessing stage before the existing security analysis pipeline.

Planned integration path:

1. Load raw logs from files, streams, or uploaded text.
2. Parse logs with `parse_log_line`.
3. Normalize parsed logs with `normalize_event`.
4. Aggregate normalized events with `aggregate_events`.
5. Send aggregated events and preserved web requests into `SecurityAgent`.
6. Use existing rule-based detection, LLM judgment, RAG explanation, and response simulation on normalized event payloads.
7. Add a user-facing workflow for reviewing parsed logs, normalized events, and final analysis results.

This keeps log ingestion deterministic while allowing `SecurityAgent` to focus on higher-level threat analysis and blue-team response guidance.
