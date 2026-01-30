# High-Level Design Checklist

A comprehensive checklist to ensure you've covered all aspects of system design.

---

## Pre-Design Checklist

### Requirements Gathered
```
□ Functional requirements documented
□ Non-functional requirements quantified
  □ Availability target (e.g., 99.9%)
  □ Latency requirements (e.g., P99 < 200ms)
  □ Throughput requirements (e.g., 10K QPS)
  □ Consistency model chosen
□ Scope boundaries defined
□ Out-of-scope items listed
```

### Estimations Complete
```
□ Traffic estimation (QPS, peak traffic)
□ Storage estimation (daily, yearly, total)
□ Bandwidth estimation
□ Cache sizing
□ Server count estimation
□ Read/write ratio identified
```

---

## Architecture Checklist

### Entry Points
```
□ DNS strategy (Route 53, Cloudflare)
□ CDN for static content
□ Load balancer configured
  □ Algorithm selected
  □ Health checks defined
  □ SSL termination
  □ Connection draining
□ API Gateway (if needed)
  □ Rate limiting
  □ Authentication
  □ Request routing
```

### Application Layer
```
□ Services identified
□ Service boundaries defined
□ Communication patterns
  □ Sync (REST, gRPC)
  □ Async (message queues)
□ Stateless design verified
□ Horizontal scaling planned
□ Auto-scaling configured
```

### Data Layer
```
□ Database type selected
□ Schema designed
□ Indexing strategy
□ Partitioning/sharding plan
□ Replication topology
□ Backup strategy
□ Data retention policy
```

### Caching Layer
```
□ Cache locations identified
□ Caching strategy selected
□ Cache invalidation approach
□ Eviction policy chosen
□ Cache sizing calculated
□ Cache failure handling
```

### Async Processing
```
□ Message queue selected
□ Topic/queue design
□ Consumer groups defined
□ Dead letter handling
□ Retry strategy
□ Ordering requirements
□ Delivery guarantees (at-least-once, etc.)
```

---

## Operational Checklist

### Monitoring & Observability
```
□ Key metrics identified
  □ Latency (P50, P95, P99)
  □ Error rate
  □ Throughput
  □ Saturation
□ Logging strategy
□ Distributed tracing
□ Alerting thresholds
□ Dashboards planned
```

### Reliability
```
□ Single points of failure eliminated
□ Failover mechanisms
□ Health check endpoints
□ Circuit breakers
□ Retry with backoff
□ Graceful degradation
□ Chaos engineering considered
```

### Security
```
□ Authentication mechanism
□ Authorization model (RBAC, etc.)
□ Encryption at rest
□ Encryption in transit
□ Secrets management
□ API security (rate limiting, validation)
□ Compliance requirements met
```

### Deployment
```
□ Deployment strategy (blue-green, canary)
□ Rollback plan
□ Database migration strategy
□ Feature flags
□ Environment parity
```

---

## Component Decision Matrix

Use this to document your choices:

```
Component          │ Choice        │ Rationale
───────────────────┼───────────────┼────────────────────────
Load Balancer      │               │
API Gateway        │               │
Primary Database   │               │
Cache              │               │
Message Queue      │               │
Object Storage     │               │
Search             │               │
CDN                │               │
Container Platform │               │
Monitoring         │               │
```

---

## Trade-offs Documentation

Document key trade-offs:

```
Trade-off 1: [Name]
├── Option A: [Description]
│   ├── Pros: ...
│   └── Cons: ...
├── Option B: [Description]
│   ├── Pros: ...
│   └── Cons: ...
└── Decision: [Choice and reasoning]

Example:
Trade-off 1: Consistency vs Availability
├── Strong Consistency (CP)
│   ├── Pros: Always accurate data
│   └── Cons: May be unavailable during partitions
├── Eventual Consistency (AP)
│   ├── Pros: Always available
│   └── Cons: May serve stale data
└── Decision: Eventual consistency for feed, strong for payments
```

---

## Bottleneck Analysis

```
Potential Bottleneck    │ Mitigation Strategy
────────────────────────┼─────────────────────────────────────
Database writes         │ Sharding, async writes, caching
Database reads          │ Read replicas, caching, denormalization
Network latency         │ CDN, edge computing, regional deployment
CPU bound               │ Horizontal scaling, optimization
Memory bound            │ Larger instances, distributed caching
Single service hotspot  │ Load balancing, rate limiting
External API limits     │ Caching, request batching, fallbacks
```

---

## Scaling Strategy

```
Component          │ Current    │ 10x Strategy         │ 100x Strategy
───────────────────┼────────────┼──────────────────────┼─────────────────
Web Servers        │ 3 servers  │ Auto-scaling to 30   │ K8s, multi-region
Database           │ 1 primary  │ Read replicas        │ Sharding
Cache              │ 1 Redis    │ Redis Cluster        │ Multi-tier caching
Message Queue      │ 1 broker   │ Kafka cluster        │ Multi-region Kafka
Object Storage     │ S3         │ S3 + CDN             │ Multi-region S3
```

---

## Failure Scenarios

Document how the system handles failures:

```
Failure Scenario          │ Impact                  │ Mitigation
──────────────────────────┼─────────────────────────┼─────────────────
Database primary fails    │ Writes unavailable      │ Auto-failover to replica
Cache cluster fails       │ Increased DB load       │ Cache bypass, DB scaling
Message queue fails       │ Async processing stops  │ Multi-broker, fallback queue
Single service fails      │ Feature unavailable     │ Circuit breaker, graceful degradation
Network partition         │ Regional unavailability │ Multi-region, async replication
```

---

## Interview Presentation Order

When presenting your design:

```
1. Requirements Recap (1 min)
   □ Key functional requirements
   □ Key NFRs with numbers

2. Estimations (2 min)
   □ Traffic numbers
   □ Storage needs
   □ Key ratios (read/write)

3. High-Level Design (5 min)
   □ Draw main components
   □ Explain data flow
   □ Call out key decisions

4. Deep Dive (15 min)
   □ Database design
   □ Scaling strategy
   □ Caching approach
   □ Handle specific scenarios

5. Trade-offs (3 min)
   □ Acknowledge alternatives
   □ Justify your choices
   □ Discuss what you'd do differently at scale

6. Wrap-up (2 min)
   □ Open questions
   □ Future improvements
```

---

## Quick Reference: Common Patterns

```
Pattern              │ When to Use
─────────────────────┼──────────────────────────────────────────
Read replicas        │ Read-heavy workload (100:1 ratio)
Sharding             │ Write-heavy or data exceeds single node
Caching              │ Repeated reads, expensive queries
CDN                  │ Static content, global users
Message queue        │ Async processing, decoupling, spikes
CQRS                 │ Different read/write patterns
Event sourcing       │ Audit trail, complex domain
Microservices        │ Team scaling, independent deployment
```

---

## Next Steps

1. → [Component Overview](component-overview.md) - Detailed component guide
2. → [Deep Dive](../06-deep-dive/) - Specific technology deep dives
3. → [Case Studies](../10-case-studies/) - See checklists applied
