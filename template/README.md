# System Design Ultimate Guide

A comprehensive, all-encompassing playbook for system design that serves as:
- **Interview Preparation**: Structured approach for system design interviews
- **Engineering Reference**: Decision frameworks for senior engineers and tech leads
- **ML/AI Guide**: Complete MLOps and ML system design patterns

---

## Quick Navigation

| Section | Description |
|---------|-------------|
| **[MASTER-TEMPLATE](MASTER-TEMPLATE.md)** | **The Ultimate Single-File Reference** |
| [01-Requirements](01-requirements/) | Functional & non-functional requirements |
| [02-Estimation](02-estimation/) | Back-of-envelope calculations |
| [03-API Design](03-api-design/) | REST, GraphQL, gRPC patterns |
| [04-Data Model](04-data-model/) | Database selection & schema design |
| [05-High-Level Design](05-high-level-design/) | Architecture components & diagrams |
| [06-Deep Dive](06-deep-dive/) | Caching, queues, security, observability |
| [07-ML Systems](07-ml-systems/) | ML pipelines, feature stores, MLOps |
| [08-Interview Template](08-interview-template/) | 45-min interview framework |
| [09-Decision Frameworks](09-decision-frameworks/) | Structured decision trees |
| [10-Case Studies](10-case-studies/) | Worked examples: Uber, Twitter, etc. |

---

## Interview Quick Reference (45 Minutes)

```
+------------------+------+----------------------------------------+
| Phase            | Time | Focus                                  |
+------------------+------+----------------------------------------+
| 1. Requirements  | 5min | Clarify scope, identify NFRs           |
| 2. Estimation    | 5min | DAU, QPS, storage, bandwidth           |
| 3. API Design    | 5min | Key endpoints, auth approach           |
| 4. High-Level    | 10min| Draw components, data flow             |
| 5. Deep Dive     | 15min| Database, scaling, caching, failures   |
| 6. Wrap-up       | 5min | Trade-offs, improvements               |
+------------------+------+----------------------------------------+
```

---

## Key Formulas Cheat Sheet

### Traffic
```
Daily Requests = DAU × actions/user/day
QPS = Daily Requests / 86,400
Peak QPS = QPS × 2 to 3 (or higher for spiky traffic)

Quick: 1M requests/day ≈ 12 QPS
```

### Storage
```
Storage = Users × data/user × retention_period × replication_factor

Quick: 1KB × 1M users = 1GB
```

### Bandwidth
```
Bandwidth = (Data size × requests/day) / 86,400 seconds
```

### Availability
```
99.9%  = 8.77 hours downtime/year
99.99% = 52.6 minutes downtime/year
```

---

## Non-Functional Requirements Checklist

| NFR | Question to Ask | Common Targets |
|-----|-----------------|----------------|
| **Availability** | What uptime SLA? | 99.9% - 99.99% |
| **Latency** | Max response time? | P99 < 100ms API |
| **Throughput** | Peak requests/sec? | Varies by system |
| **Consistency** | Strong or eventual? | Use case dependent |
| **Durability** | Can we lose data? | 11 9s for critical |
| **Scalability** | 10x growth plan? | Horizontal preferred |

---

## Database Selection Quick Guide

```
Need ACID transactions?
├── Yes → SQL (PostgreSQL, MySQL)
└── No → Continue...

Need flexible schema?
├── Yes → Document DB (MongoDB)
└── No → Continue...

High write throughput?
├── Yes → Wide Column (Cassandra) or KV Store
└── No → Continue...

Simple key-value access?
├── Yes → Redis, DynamoDB
└── No → SQL or Document DB
```

---

## Architecture Template

```
                                    ┌─────────────┐
                                    │   Clients   │
                                    │ (Web/Mobile)│
                                    └──────┬──────┘
                                           │
                                    ┌──────▼──────┐
                                    │     CDN     │
                                    │(Static/Edge)│
                                    └──────┬──────┘
                                           │
                                    ┌──────▼──────┐
                                    │    Load     │
                                    │  Balancer   │
                                    └──────┬──────┘
                                           │
                                    ┌──────▼──────┐
                                    │ API Gateway │
                                    │(Auth/Route) │
                                    └──────┬──────┘
                                           │
              ┌────────────────────────────┼────────────────────────────┐
              │                            │                            │
       ┌──────▼──────┐              ┌──────▼──────┐              ┌──────▼──────┐
       │  Service A  │              │  Service B  │              │  Service C  │
       └──────┬──────┘              └──────┬──────┘              └──────┬──────┘
              │                            │                            │
              └────────────────────────────┼────────────────────────────┘
                                           │
              ┌────────────────────────────┼────────────────────────────┐
              │                            │                            │
       ┌──────▼──────┐              ┌──────▼──────┐              ┌──────▼──────┐
       │    Cache    │              │  Database   │              │   Message   │
       │   (Redis)   │              │ (SQL/NoSQL) │              │    Queue    │
       └─────────────┘              └─────────────┘              └──────┬──────┘
                                                                        │
                                                                 ┌──────▼──────┐
                                                                 │   Workers   │
                                                                 │ (Async Jobs)│
                                                                 └─────────────┘
```

---

## How to Use This Guide

### For Interview Prep
1. **Start with [MASTER-TEMPLATE](MASTER-TEMPLATE.md)** - Your single-file ultimate reference
2. Study [10-Case Studies](10-case-studies/) for worked examples
3. Use [09-Decision Frameworks](09-decision-frameworks/) for trade-off discussions
4. Review [08-Interview Template](08-interview-template/) for timing and structure

### For Real-World Design
1. Begin with [01-Requirements](01-requirements/) to scope the problem
2. Use [02-Estimation](02-estimation/) for capacity planning
3. Reference [06-Deep Dive](06-deep-dive/) for implementation details

### For ML Systems
1. See [07-ML Systems](07-ml-systems/) for complete MLOps coverage
2. Includes feature stores, model serving, A/B testing, monitoring

---

## Key Principles

1. **Clarify Before Designing**: Always understand requirements first
2. **Start Simple**: Begin with a basic design, then iterate
3. **Identify Bottlenecks**: Find the limiting factor early
4. **Discuss Trade-offs**: Every decision has pros and cons
5. **Think About Failure**: Design for what goes wrong
6. **Consider Operations**: Monitoring, deployment, debugging

---

## Contributing

This guide is structured for easy extension. Each section follows a consistent format:
- Overview and key concepts
- Decision questions to ask
- Trade-offs and considerations
- Checklists and quick references
- Practical examples

---

*Last Updated: January 2025*
