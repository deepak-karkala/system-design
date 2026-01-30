# Observability Deep Dive

Understanding and monitoring complex distributed systems through logs, metrics, and traces.

---

## The Three Pillars

```
┌────────────────────────────────────────────────────────────────┐
│                     OBSERVABILITY                               │
├──────────────────┬──────────────────┬──────────────────────────┤
│      LOGS        │     METRICS      │        TRACES            │
├──────────────────┼──────────────────┼──────────────────────────┤
│ What happened?   │ How is it doing? │ Where did time go?       │
│ Discrete events  │ Numeric values   │ Request journey          │
│ High cardinality │ Low cardinality  │ Causality                │
│ Debug, audit     │ Alert, dashboard │ Performance analysis     │
└──────────────────┴──────────────────┴──────────────────────────┘
```

---

## Logs

### Structured Logging

```
Unstructured (bad):
  2024-01-15 10:30:00 User john logged in from 1.2.3.4

Structured (good):
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "event": "user_login",
  "user_id": "john",
  "ip": "1.2.3.4",
  "request_id": "req-abc123",
  "service": "auth-service",
  "version": "1.2.3"
}

Benefits:
  ✓ Searchable and filterable
  ✓ Parseable by machines
  ✓ Consistent format
  ✓ Easy correlation
```

### Log Levels

```
Level   │ When to Use                        │ Example
────────┼────────────────────────────────────┼────────────────────
DEBUG   │ Development, troubleshooting       │ Variable values
INFO    │ Normal operations, milestones      │ Request completed
WARN    │ Potential issues, degradation      │ Slow query, retry
ERROR   │ Failures requiring attention       │ Exception caught
FATAL   │ System cannot continue             │ Cannot start

Production:
  - Usually INFO and above
  - DEBUG on demand for troubleshooting
```

### Logging Architecture

```
┌─────────┐    ┌─────────┐    ┌─────────┐
│Service A│    │Service B│    │Service C│
└────┬────┘    └────┬────┘    └────┬────┘
     │              │              │
     │ stdout/file  │              │
     ▼              ▼              ▼
┌────────────────────────────────────────┐
│         Log Collector (Fluentd)        │
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│    Log Aggregator (Elasticsearch)       │
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│       Visualization (Kibana)            │
└────────────────────────────────────────┘

ELK Stack:
  - Elasticsearch: Storage and search
  - Logstash/Fluentd: Collection and processing
  - Kibana: Visualization

Alternatives:
  - Splunk
  - Datadog
  - CloudWatch Logs
  - Loki + Grafana
```

### Best Practices

```
DO:
  ✓ Use structured logging (JSON)
  ✓ Include request/correlation ID
  ✓ Log at appropriate levels
  ✓ Include context (user, service, version)
  ✓ Set retention policies

DON'T:
  ✗ Log sensitive data (passwords, PII)
  ✗ Log in hot loops (performance)
  ✗ Use print statements in production
  ✗ Log entire request/response bodies
```

---

## Metrics

### Types of Metrics

```
Counter:
  - Only increases (or resets)
  - Example: requests_total, errors_total
  - Use: Count events

Gauge:
  - Can go up or down
  - Example: cpu_usage, memory_usage
  - Use: Current state

Histogram:
  - Distribution of values
  - Example: request_duration_seconds
  - Use: Latency percentiles

Summary:
  - Pre-calculated percentiles
  - Example: request_duration_quantile
  - Use: Client-side percentiles
```

### The Four Golden Signals (Google SRE)

```
1. Latency:
   - Time to service a request
   - Distinguish success vs failure latency
   - Track: P50, P95, P99

2. Traffic:
   - Demand on the system
   - Requests per second
   - Track: QPS by endpoint, method

3. Errors:
   - Rate of failed requests
   - HTTP 5xx, exceptions
   - Track: Error rate, error types

4. Saturation:
   - How "full" the system is
   - CPU, memory, disk, queue depth
   - Track: Resource utilization
```

### RED Method (Microservices)

```
Rate:     Requests per second
Errors:   Failed requests per second
Duration: Time per request (latency)

For every service, track:
  http_requests_total{service="api", status="200"}
  http_request_duration_seconds{service="api"}
```

### USE Method (Resources)

```
Utilization: How busy is the resource?
Saturation:  Queue length or wait time
Errors:      Error events

For each resource (CPU, memory, disk, network):
  cpu_usage_percent
  memory_available_bytes
  disk_io_queue_length
  network_errors_total
```

### Prometheus + Grafana

```
Prometheus Architecture:
  ┌─────────────────────────────────────────────────────────────┐
  │                       Prometheus                             │
  │  ┌─────────────────┐    ┌──────────────────┐               │
  │  │   Scrape Jobs   │───>│    Time Series   │               │
  │  │   (pull model)  │    │      Database    │               │
  │  └─────────────────┘    └──────────────────┘               │
  │            │                     │                          │
  │            ▼                     ▼                          │
  │  ┌─────────────────┐    ┌──────────────────┐               │
  │  │  Service        │    │    Alertmanager  │               │
  │  │  Discovery      │    │                  │               │
  │  └─────────────────┘    └──────────────────┘               │
  └─────────────────────────────────────────────────────────────┘

PromQL Examples:
  # Request rate (5 min average)
  rate(http_requests_total[5m])

  # Error rate
  rate(http_requests_total{status=~"5.."}[5m])
  / rate(http_requests_total[5m])

  # P99 latency
  histogram_quantile(0.99,
    rate(http_request_duration_seconds_bucket[5m]))
```

---

## Distributed Tracing

### Concepts

```
Trace: End-to-end journey of a request
Span: Single operation within a trace
Context: Propagated data (trace ID, span ID)

Example trace:
  Trace ID: abc123
  ├── Span: API Gateway (50ms)
  │   ├── Span: Auth Service (10ms)
  │   └── Span: User Service (30ms)
  │       └── Span: Database Query (15ms)
  └── Total: 50ms
```

### Trace Visualization

```
┌─────────────────────────────────────────────────────────────────┐
│ Trace: abc123                                          100ms    │
├─────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ API Gateway                                         60ms │   │
│ └──────────────────────────────────────────────────────────┘   │
│    ┌────────────────────────────────────────────────────┐      │
│    │ Auth Service                                  15ms │      │
│    └────────────────────────────────────────────────────┘      │
│       ┌─────────────────────────────────────────────────┐     │
│       │ Order Service                              40ms │     │
│       └─────────────────────────────────────────────────┘     │
│          ┌──────────────────────────────────────────┐         │
│          │ Database                           20ms │         │
│          └──────────────────────────────────────────┘         │
│             ┌───────────────────────────────────┐             │
│             │ Cache                        5ms │             │
│             └───────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### Context Propagation

```
HTTP Headers (W3C Trace Context):
  traceparent: 00-abc123-def456-01
  tracestate: vendor1=value1

Propagation across services:
  Service A ──header──> Service B ──header──> Service C

Code example:
  def handle_request(request):
      # Extract context from incoming request
      context = tracer.extract(request.headers)

      with tracer.start_span("operation", context=context) as span:
          # Add span attributes
          span.set_attribute("user.id", user_id)

          # Call downstream service with propagated context
          headers = tracer.inject(span.context)
          response = call_service_b(headers)
```

### OpenTelemetry

```
Unified observability framework:
  - Single API for traces, metrics, logs
  - Vendor-agnostic
  - Auto-instrumentation available

Components:
  - API: Instrumentation interface
  - SDK: Implementation
  - Collector: Receive, process, export
  - Exporters: Send to backends (Jaeger, Zipkin, etc.)

Architecture:
  ┌─────────┐    ┌─────────────────┐    ┌─────────────┐
  │ Service │───>│ OTel Collector  │───>│   Jaeger    │
  │ (SDK)   │    │ (process/batch) │    │   Zipkin    │
  └─────────┘    └─────────────────┘    │   Datadog   │
                                         └─────────────┘
```

---

## Alerting

### Alert Design

```
Good alerts:
  ✓ Actionable (someone needs to do something)
  ✓ Urgent (needs attention now)
  ✓ Clear (what's wrong, impact, next steps)
  ✓ Infrequent (not noise)

Bad alerts:
  ✗ "CPU at 80%" (not necessarily a problem)
  ✗ Flapping alerts (on-off-on-off)
  ✗ Duplicate alerts for same issue
  ✗ Alerts no one acts on
```

### Alert Levels

```
Level    │ Response Time │ Example
─────────┼───────────────┼────────────────────────────────
P1/SEV1  │ Immediate     │ Complete outage, data loss
P2/SEV2  │ < 1 hour      │ Degraded service, errors > 5%
P3/SEV3  │ < 4 hours     │ Non-critical feature down
P4/SEV4  │ Next day      │ Cosmetic issues, minor bugs
```

### SLI/SLO/SLA

```
SLI (Service Level Indicator):
  - Measurable aspect of service
  - Example: Request latency P99

SLO (Service Level Objective):
  - Target value for SLI
  - Example: P99 latency < 200ms

SLA (Service Level Agreement):
  - Contract with consequences
  - Example: 99.9% availability or credit

Error Budget:
  - Allowed downtime/errors
  - 99.9% SLO = 0.1% error budget
  - = 43.8 minutes/month downtime allowed

Alerting on error budget burn rate:
  - If consuming budget too fast, alert
  - Allows occasional errors without paging
```

---

## Dashboards

### Dashboard Structure

```
Overview Dashboard:
  Row 1: Key business metrics (users, revenue, orders)
  Row 2: Golden signals (latency, traffic, errors, saturation)
  Row 3: Service health (up/down, versions)

Service Dashboard:
  Row 1: Traffic (QPS, by endpoint)
  Row 2: Latency (P50, P95, P99 over time)
  Row 3: Errors (rate, by type)
  Row 4: Resources (CPU, memory, connections)

Infrastructure Dashboard:
  Row 1: Cluster health (nodes, pods)
  Row 2: Resource utilization
  Row 3: Network metrics
  Row 4: Storage metrics
```

### Dashboard Best Practices

```
DO:
  ✓ Start with golden signals
  ✓ Use consistent time ranges
  ✓ Include context (SLO lines, annotations)
  ✓ Link to runbooks from alerts
  ✓ Show historical comparison

DON'T:
  ✗ Create dashboards no one uses
  ✗ Show raw numbers without context
  ✗ Use misleading scales
  ✗ Overcrowd with too many panels
```

---

## Debugging Workflow

```
1. Detect:
   - Alert fires or user reports issue
   - Check dashboard for anomalies

2. Triage:
   - What is the impact?
   - When did it start?
   - Is it getting worse?

3. Investigate:
   - Check metrics for symptoms
   - Find relevant traces
   - Search logs for errors

4. Correlate:
   - Use request ID across services
   - Compare to last deploy
   - Check for infrastructure changes

5. Resolve:
   - Apply fix or rollback
   - Verify recovery
   - Document in post-mortem
```

---

## Interview Tips

### Questions to Ask

```
1. What are the key business metrics?
   → Determines what to monitor

2. What's the latency requirement?
   → Sets SLO targets

3. How is the system debugged today?
   → Existing observability gaps

4. What's the scale?
   → Log/metric volume considerations

5. What's the alert response process?
   → Determines alert design
```

### Key Points to Discuss

```
✓ Three pillars (logs, metrics, traces)
✓ Golden signals or RED/USE method
✓ Structured logging with correlation IDs
✓ Distributed tracing for request flow
✓ SLI/SLO-based alerting
✓ Dashboard hierarchy
✓ Incident response workflow
```

---

## Next Steps

1. → [Fault Tolerance](fault-tolerance.md) - Detect and recover
2. → [Security](security.md) - Security monitoring
3. → [Case Studies](../10-case-studies/) - See observability in practice
