# Non-Functional Requirements (NFRs)

Non-functional requirements define **how** the system should behave - the quality attributes that determine system performance, reliability, and usability.

---

## Overview

NFRs answer: "How well should the system perform?"

They describe:
- Performance characteristics (speed, capacity)
- Reliability expectations (uptime, fault tolerance)
- Security requirements (authentication, encryption)
- Operational concerns (monitoring, maintenance)

**Key Insight:** NFRs often conflict with each other. Understanding trade-offs is critical.

---

## The Big 8 Non-Functional Requirements

### 1. Availability

**Definition:** The percentage of time the system is operational and accessible.

**Key Questions:**
- What uptime SLA is required?
- What is the cost of downtime (business impact)?
- Is 24/7 availability needed or only during business hours?
- What is the acceptable planned maintenance window?

**Availability Targets:**
```
Availability  | Downtime/Year | Downtime/Month | Downtime/Week
--------------|---------------|----------------|---------------
99%           | 3.65 days     | 7.31 hours     | 1.68 hours
99.9%         | 8.77 hours    | 43.83 minutes  | 10.08 minutes
99.95%        | 4.38 hours    | 21.92 minutes  | 5.04 minutes
99.99%        | 52.60 minutes | 4.38 minutes   | 1.01 minutes
99.999%       | 5.26 minutes  | 26.30 seconds  | 6.05 seconds
```

**Design Implications:**
- 99.9% → Single region, basic redundancy
- 99.99% → Multi-AZ, automated failover, no single points of failure
- 99.999% → Multi-region, active-active, extensive testing

**Trade-offs:**
- Higher availability → More complexity and cost
- Higher availability → Often sacrifices consistency (CAP theorem)

---

### 2. Scalability

**Definition:** The ability to handle growth in users, data, or traffic.

**Key Questions:**
- How many users today? Expected in 1 year? 5 years?
- What is the peak vs average traffic ratio?
- Is growth gradual or can there be sudden spikes?
- Should we scale horizontally or vertically?

**Scalability Dimensions:**
```
Dimension        | Examples                      | Scaling Strategy
-----------------|-------------------------------|------------------
User Growth      | 1M → 100M users               | Horizontal scaling
Data Volume      | 1TB → 1PB storage             | Sharding, tiered storage
Traffic Spikes   | 10x during events             | Auto-scaling, CDN
Geographic       | Single region → Global        | Multi-region, edge
Complexity       | Simple → Complex queries      | Read replicas, caching
```

**Design Implications:**
- Stateless services for horizontal scaling
- Database sharding strategies
- Caching layers
- Async processing for load leveling

**Trade-offs:**
- Horizontal scaling → More operational complexity
- Scaling → Higher cost
- Distributed systems → Consistency challenges

---

### 3. Latency (Performance)

**Definition:** The time it takes to respond to a request.

**Key Questions:**
- What is the acceptable P50, P95, P99 latency?
- Is real-time response required?
- What are the latency requirements for different operations?
- Where are users located geographically?

**Latency Targets by Use Case:**
```
Use Case                | Target Latency
------------------------|----------------
Real-time gaming        | < 50ms
Interactive UI          | < 100ms
API response            | < 200ms
Page load               | < 1 second
Background jobs         | < 1 minute
Batch processing        | Hours acceptable
```

**Latency Breakdown:**
```
Total Latency = Network + Server Processing + Database + External APIs

Network:
  - Same region:     ~1-5ms
  - Cross-region:    ~50-150ms
  - Intercontinental: ~100-300ms

Database:
  - Cached query:    ~1ms
  - Simple query:    ~5-20ms
  - Complex join:    ~50-500ms
```

**Design Implications:**
- CDN for static content
- Edge computing for real-time needs
- Caching at multiple levels
- Database indexing and query optimization
- Async processing for non-critical paths

**Trade-offs:**
- Lower latency → Higher infrastructure cost
- Lower latency → May need to relax consistency
- Lower latency → More caching complexity

---

### 4. Throughput

**Definition:** The number of operations the system can handle per unit time.

**Key Questions:**
- What is the expected requests per second (RPS)?
- What is the read vs write ratio?
- Are there batch operations to consider?
- What is peak throughput vs average?

**Throughput Estimation:**
```
Daily Active Users (DAU) × Actions/User/Day = Daily Operations
Daily Operations ÷ 86,400 = Average Operations/Second

Peak = Average × Peak Factor (typically 2-5x)
```

**Example:**
```
Service: Twitter-like Platform

DAU: 100M users
Actions: 20 reads + 2 writes per user per day

Read throughput:
  100M × 20 = 2B reads/day
  2B ÷ 86,400 = ~23,000 reads/sec (average)
  Peak: 23K × 3 = ~70,000 reads/sec

Write throughput:
  100M × 2 = 200M writes/day
  200M ÷ 86,400 = ~2,300 writes/sec (average)
  Peak: 2.3K × 3 = ~7,000 writes/sec
```

**Design Implications:**
- Read-heavy → Read replicas, heavy caching
- Write-heavy → Sharding, async writes, write-behind cache
- High throughput → Load balancing, connection pooling

---

### 5. Consistency

**Definition:** Whether all users see the same data at the same time.

**Key Questions:**
- Is eventual consistency acceptable?
- How stale can the data be?
- Are there operations requiring strong consistency?
- What happens if users see different data?

**Consistency Models:**
```
Model               | Description                     | Use Case
--------------------|--------------------------------|------------
Strong Consistency  | All reads see latest write     | Banking, inventory
Eventual Consistency| Reads eventually see write     | Social media, DNS
Causal Consistency  | Related operations are ordered | Messaging
Read-your-writes    | User sees their own writes     | User profiles
```

**Example Decisions:**
```
Strong Consistency Required:
  - Financial transactions
  - Inventory counts (prevent overselling)
  - User authentication
  - Configuration updates

Eventual Consistency Acceptable:
  - Like counts on posts
  - Follower counts
  - News feed updates
  - Analytics data
```

**Design Implications:**
- Strong consistency → Single leader, synchronous replication
- Eventual consistency → Multi-leader, async replication
- Mixed → Different consistency for different data

**Trade-offs (CAP Theorem):**
- Strong consistency → Lower availability during partitions
- Eventual consistency → Potential for stale reads

---

### 6. Durability

**Definition:** Guarantee that written data will not be lost.

**Key Questions:**
- What is the acceptable data loss window?
- How critical is each data type?
- What are the backup and recovery requirements?
- What is the Recovery Point Objective (RPO)?

**Durability Levels:**
```
Level                | Data Loss Risk      | Implementation
---------------------|---------------------|------------------
No durability        | All data at risk    | In-memory only
Single disk          | Disk failure = loss | Local storage
Replicated           | Multi-failure safe  | 3+ replicas
Geo-replicated       | Region failure safe | Cross-region copies
```

**Key Metrics:**
```
RPO (Recovery Point Objective):
  - How much data loss is acceptable?
  - Seconds (sync replication) → Hours (daily backups)

RTO (Recovery Time Objective):
  - How quickly must we recover?
  - Seconds (hot standby) → Hours (cold backup restore)
```

**Design Implications:**
- Synchronous replication for zero data loss
- Write-ahead logging
- Regular backups with tested recovery
- Multiple storage tiers

---

### 7. Security

**Definition:** Protection of data and systems from unauthorized access.

**Key Questions:**
- What data is sensitive? (PII, financial, health)
- What compliance requirements exist? (GDPR, HIPAA, SOC2)
- What authentication methods are required?
- Is encryption at rest and in transit required?

**Security Checklist:**
```
Authentication:
  [ ] Multi-factor authentication (MFA)
  [ ] OAuth 2.0 / OpenID Connect
  [ ] Session management
  [ ] Password policies

Authorization:
  [ ] Role-based access control (RBAC)
  [ ] Least privilege principle
  [ ] API authentication (JWT, API keys)

Data Protection:
  [ ] Encryption at rest
  [ ] Encryption in transit (TLS)
  [ ] Data masking/anonymization
  [ ] Secrets management

Infrastructure:
  [ ] Network segmentation
  [ ] Firewall rules
  [ ] DDoS protection
  [ ] Audit logging
```

**Compliance Requirements:**
```
Regulation | Focus Area              | Key Requirements
-----------|-------------------------|------------------
GDPR       | EU data privacy         | Consent, data deletion
HIPAA      | US health data          | PHI protection, audit
PCI DSS    | Payment card data       | Encryption, access control
SOC 2      | Service organizations   | Security, availability
```

---

### 8. Reliability

**Definition:** The ability to function correctly and consistently over time.

**Key Questions:**
- What is the acceptable failure rate?
- How should the system behave during partial failures?
- What is the Mean Time Between Failures (MTBF)?
- What is the Mean Time To Recovery (MTTR)?

**Reliability Patterns:**
```
Pattern              | Description                    | Implementation
---------------------|--------------------------------|----------------
Redundancy           | Multiple instances             | Multi-AZ deployment
Failover             | Switch to backup               | Load balancer health checks
Graceful degradation | Reduced functionality          | Feature flags, fallbacks
Circuit breaker      | Prevent cascade failures       | Hystrix pattern
Retry with backoff   | Handle transient failures      | Exponential backoff
```

**Design Implications:**
- No single points of failure
- Health checks and monitoring
- Chaos engineering for testing
- Runbooks for incident response

---

## NFR Trade-off Matrix

Understanding how NFRs interact:

```
                  Availability | Consistency | Latency | Cost
------------------|-------------|-------------|---------|------
Availability      |      -      |     ↓       |    ↔    |  ↑
Consistency       |      ↓      |      -      |    ↑    |  ↔
Latency           |      ↔      |     ↓       |     -   |  ↑
Scalability       |      ↔      |     ↓       |    ↓    |  ↑
Durability        |      ↑      |     ↑       |    ↑    |  ↑
Security          |      ↓      |     ↔       |    ↑    |  ↑

↑ = Increases  ↓ = Decreases  ↔ = Trade-off dependent
```

---

## Interview Tips

### Questions to Ask
1. "What is the expected scale - DAU, QPS?"
2. "What latency is acceptable for the critical path?"
3. "Is eventual consistency acceptable or do we need strong consistency?"
4. "What is the availability requirement - 99.9% or higher?"
5. "Are there any compliance requirements?"
6. "What is the budget constraint?"

### How to Discuss NFRs
1. **Prioritize**: Not all NFRs are equally important - identify the top 2-3
2. **Quantify**: Use specific numbers, not vague terms
3. **Trade-off**: Explain what you're sacrificing for each choice
4. **Justify**: Connect NFR choices to business requirements

### Common Mistakes
- Treating all NFRs as equally important
- Not quantifying requirements
- Ignoring trade-offs
- Over-engineering for requirements that don't exist

---

## NFR Requirements Template

```markdown
# Non-Functional Requirements

## Availability
- Target: 99.9% uptime
- Planned maintenance window: Sunday 2-4 AM UTC
- Maximum unplanned downtime: 8.77 hours/year

## Performance
- API latency P99: < 200ms
- Page load time: < 2 seconds
- Peak throughput: 10,000 RPS

## Scalability
- Current: 1M DAU
- 1-year projection: 10M DAU
- Scaling approach: Horizontal auto-scaling

## Consistency
- User data: Strong consistency
- Feed data: Eventual consistency (< 5 seconds)
- Analytics: Eventual consistency (< 1 minute)

## Security
- Authentication: OAuth 2.0 + MFA
- Encryption: TLS 1.3 in transit, AES-256 at rest
- Compliance: SOC 2 Type II

## Durability
- RPO: 0 for transactions, 1 hour for analytics
- RTO: 15 minutes
- Backup: Hourly incremental, daily full
```

---

## Next Steps

After defining NFRs:
1. → [Estimation](../02-estimation/) - Calculate capacity requirements
2. → [Data Model](../04-data-model/) - Choose databases based on NFRs
3. → [Deep Dive](../06-deep-dive/) - Design for specific NFRs
