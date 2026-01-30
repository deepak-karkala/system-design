# System Design Master Template

**The Ultimate Playbook for Any System Design Problem**

This single file contains ALL factors, questions, trade-offs, heuristics, and mental models needed to approach any system design interview. Use this as your go-to reference and checklist.

---

## Table of Contents

1. [Interview Framework (45 min)](#1-interview-framework-45-min)
2. [Requirements Phase](#2-requirements-phase)
3. [Estimation Phase](#3-estimation-phase)
4. [API Design Phase](#4-api-design-phase)
5. [Data Model Phase](#5-data-model-phase)
6. [High-Level Design Phase](#6-high-level-design-phase)
7. [Deep Dive Phase](#7-deep-dive-phase)
8. [ML Systems Considerations](#8-ml-systems-considerations)
9. [Trade-offs Master List](#9-trade-offs-master-list)
10. [Heuristics & Rules of Thumb](#10-heuristics--rules-of-thumb)
11. [Mental Models](#11-mental-models)
12. [Common Mistakes to Avoid](#12-common-mistakes-to-avoid)

---

## 1. Interview Framework (45 min)

```
┌────────────────────────────────────────────────────────────────┐
│  PHASE 1: REQUIREMENTS (5 min)                                 │
│  ─────────────────────────────                                 │
│  • Clarify functional requirements (what)                      │
│  • Identify non-functional requirements (how well)             │
│  • Define scope boundaries (in/out of scope)                   │
│  • Identify core use cases (2-3 main flows)                    │
├────────────────────────────────────────────────────────────────┤
│  PHASE 2: ESTIMATION (5 min)                                   │
│  ──────────────────────────                                    │
│  • Users (DAU/MAU)                                             │
│  • Traffic (QPS, peak QPS)                                     │
│  • Storage (per user, total, growth)                           │
│  • Bandwidth (ingress/egress)                                  │
├────────────────────────────────────────────────────────────────┤
│  PHASE 3: API DESIGN (5 min)                                   │
│  ─────────────────────────                                     │
│  • Define key endpoints (3-5 core APIs)                        │
│  • Choose protocol (REST/GraphQL/gRPC/WebSocket)               │
│  • Authentication approach                                     │
│  • Rate limiting strategy                                      │
├────────────────────────────────────────────────────────────────┤
│  PHASE 4: HIGH-LEVEL DESIGN (10 min)                           │
│  ───────────────────────────────────                           │
│  • Draw architecture diagram                                   │
│  • Identify all components                                     │
│  • Show data flow                                              │
│  • Identify data stores                                        │
├────────────────────────────────────────────────────────────────┤
│  PHASE 5: DEEP DIVE (15 min)                                   │
│  ──────────────────────────                                    │
│  • Database schema and choices                                 │
│  • Scaling strategies                                          │
│  • Caching approach                                            │
│  • Handle failures and edge cases                              │
│  • Deep dive into 1-2 critical components                      │
├────────────────────────────────────────────────────────────────┤
│  PHASE 6: WRAP-UP (5 min)                                      │
│  ─────────────────────────                                     │
│  • Summarize key trade-offs                                    │
│  • Discuss bottlenecks                                         │
│  • Future improvements                                         │
│  • Monitoring and observability                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 2. Requirements Phase

### 2.1 Functional Requirements - Questions to Ask

```
USERS & ACTORS
□ Who are the users? (consumers, businesses, admins, systems)
□ How many user types/roles?
□ Is this B2C, B2B, or internal?

CORE FEATURES - Ask for each:
□ What is the primary use case?
□ What are the secondary use cases?
□ What can we explicitly exclude?

USER JOURNEY
□ What is the happy path flow?
□ What actions can a user perform?
□ What data does a user see?

DATA
□ What data is created?
□ What data is read?
□ What data is updated/deleted?
□ Who owns the data?

INTERACTIONS
□ Is it read-heavy or write-heavy?
□ Does it need real-time updates?
□ Does it need offline support?
□ Does it need multi-device sync?
```

### 2.2 Non-Functional Requirements - Complete Checklist

```
AVAILABILITY
□ What uptime is required? (99.9%, 99.99%, 99.999%)
□ Is 24/7 availability needed?
□ Can we have scheduled maintenance windows?
□ What's the cost of downtime?

LATENCY
□ What's acceptable response time? (p50, p99)
□ Is real-time required? (< 100ms)
□ Interactive? (< 1 second)
□ Background acceptable? (seconds to minutes)

THROUGHPUT
□ Expected requests per second?
□ Peak vs average traffic ratio?
□ Seasonal or event-driven spikes?
□ Growth projections (6 months, 1 year, 5 years)?

CONSISTENCY
□ Strong consistency required? (banking, inventory)
□ Eventual consistency acceptable? (social feeds)
□ What's acceptable staleness window?
□ Read-your-writes needed?

DURABILITY
□ Can we lose any data?
□ What data is critical vs reconstructable?
□ Backup and recovery requirements?
□ Retention period?

SCALABILITY
□ Expected user growth?
□ Expected data growth?
□ Horizontal vs vertical scaling preference?
□ Multi-region requirements?

SECURITY
□ Authentication requirements?
□ Authorization model (RBAC, ABAC)?
□ Encryption requirements (at rest, in transit)?
□ Compliance requirements (GDPR, HIPAA, PCI)?

RELIABILITY
□ Acceptable error rate?
□ Graceful degradation requirements?
□ Retry and recovery expectations?

COST
□ Budget constraints?
□ Cost vs performance trade-offs?
□ Optimize for which metric?
```

### 2.3 Scope Definition Template

```
IN SCOPE:
• Feature 1: [description]
• Feature 2: [description]
• Feature 3: [description]

OUT OF SCOPE (acknowledge but exclude):
• Feature X: [reason]
• Feature Y: [reason]

ASSUMPTIONS:
• Assumption 1
• Assumption 2
```

---

## 3. Estimation Phase

### 3.1 Traffic Estimation

```
STEP 1: START WITH USERS
□ Monthly Active Users (MAU)
□ Daily Active Users (DAU) - typically 10-50% of MAU
□ Concurrent users at peak - typically 10-20% of DAU

STEP 2: CALCULATE ACTIONS
□ Actions per user per day
□ Daily actions = DAU × actions/user
□ Requests per second = Daily actions / 86,400

STEP 3: ACCOUNT FOR PEAKS
□ Peak multiplier (2-10x average)
□ Consider time zones, events, seasonality

QUICK FORMULAS:
• 1M requests/day ≈ 12 QPS
• 100M requests/day ≈ 1,200 QPS
• 1B requests/day ≈ 12,000 QPS
```

### 3.2 Storage Estimation

```
STEP 1: ESTIMATE PER-ITEM SIZE
□ Text data: count characters/fields
□ Media: define quality and dimensions
□ Metadata: fixed overhead per item

STEP 2: CALCULATE VOLUME
□ Items created per day
□ Retention period
□ Total items = daily × retention

STEP 3: APPLY MULTIPLIERS
□ Replication factor (typically 3x)
□ Index overhead (typically 20-30%)
□ Working space (typically 20%)

SIZE REFERENCE:
• 1 character = 1 byte (ASCII) or 2-4 bytes (UTF-8)
• 1 integer = 4-8 bytes
• UUID = 16 bytes
• Timestamp = 8 bytes
• Small JSON object = 500 bytes - 2 KB
• Profile photo = 200 KB - 1 MB
• High-res image = 2-5 MB
• 1-min video (720p) = 50-100 MB
```

### 3.3 Bandwidth Estimation

```
INGRESS (data coming in):
□ Upload size × upload frequency

EGRESS (data going out):
□ Download size × download frequency
□ Note: Egress typically >> Ingress

FORMULA:
Bandwidth = (size × requests) / time_period

QUICK REFERENCE:
• 1 Mbps = 125 KB/s = 10.8 GB/day
• 1 Gbps = 125 MB/s = 10.8 TB/day
```

### 3.4 Memory/Cache Estimation

```
CACHE SIZING:
□ What % of data is hot? (typically 20%)
□ Cache = Total_data × hot_data_percentage
□ Account for cache overhead (keys, metadata)

RULE OF THUMB:
• Cache the 20% most frequently accessed data
• A single Redis node handles ~100K ops/sec
• Each Redis node: 25-50 GB usable memory
```

---

## 4. API Design Phase

### 4.1 Protocol Selection

```
REST - Choose when:
□ CRUD operations
□ Public APIs
□ Caching important
□ Stateless operations
□ Wide client compatibility needed

GraphQL - Choose when:
□ Complex, nested data
□ Multiple client types with different needs
□ Bandwidth efficiency critical (mobile)
□ Rapid iteration on data requirements

gRPC - Choose when:
□ Internal service-to-service communication
□ High performance required
□ Strong typing important
□ Streaming needed
□ Polyglot environment

WebSocket - Choose when:
□ Real-time bidirectional communication
□ Push notifications
□ Live updates (chat, gaming, collaboration)
□ Long-lived connections acceptable
```

### 4.2 API Design Checklist

```
ENDPOINT DESIGN
□ Use nouns for resources (users, orders)
□ Use HTTP verbs correctly (GET, POST, PUT, DELETE)
□ Use plural nouns (/users not /user)
□ Nest resources logically (/users/{id}/orders)
□ Version your API (/v1/users)

REQUEST/RESPONSE
□ Use appropriate status codes
□ Return consistent response format
□ Include pagination for lists
□ Support filtering and sorting
□ Use appropriate content types

AUTHENTICATION
□ API keys (simple, less secure)
□ JWT tokens (stateless, scalable)
□ OAuth 2.0 (third-party access)
□ Session-based (stateful, simpler)

RATE LIMITING
□ Per-user limits
□ Per-IP limits
□ Per-API-key limits
□ Return rate limit headers
□ Implement graceful degradation

PAGINATION
□ Cursor-based (recommended for large datasets)
□ Offset-based (simple but has issues at scale)
□ Include total count (optional, expensive)
□ Consistent page size

ERROR HANDLING
□ Standard error format
□ Meaningful error messages
□ Error codes for programmatic handling
□ Don't expose internal details
```

### 4.3 Common Status Codes

```
2xx SUCCESS
• 200 OK - Success
• 201 Created - Resource created
• 204 No Content - Success, no body

4xx CLIENT ERROR
• 400 Bad Request - Invalid input
• 401 Unauthorized - Not authenticated
• 403 Forbidden - Not authorized
• 404 Not Found - Resource doesn't exist
• 409 Conflict - Resource conflict
• 429 Too Many Requests - Rate limited

5xx SERVER ERROR
• 500 Internal Server Error - Generic error
• 502 Bad Gateway - Upstream error
• 503 Service Unavailable - Temporarily down
• 504 Gateway Timeout - Upstream timeout
```

---

## 5. Data Model Phase

### 5.1 Database Selection Decision Tree

```
START HERE
    │
    ▼
Need ACID transactions?
├── Yes → Need complex queries/joins?
│         ├── Yes → PostgreSQL
│         └── No → Consider PostgreSQL or MySQL
│
└── No → What's the access pattern?
          │
          ├── Key-Value lookups
          │   └── Redis (cache), DynamoDB (persistent)
          │
          ├── Document storage (flexible schema)
          │   └── MongoDB, Couchbase
          │
          ├── Wide-column (high write throughput)
          │   └── Cassandra, HBase, ScyllaDB
          │
          ├── Time-series data
          │   └── InfluxDB, TimescaleDB
          │
          ├── Full-text search
          │   └── Elasticsearch, OpenSearch
          │
          ├── Graph relationships
          │   └── Neo4j, Amazon Neptune
          │
          └── Analytics/OLAP
              └── ClickHouse, BigQuery, Snowflake
```

### 5.2 Database Trade-offs Matrix

```
┌─────────────────┬────────────────┬────────────────┬────────────────┐
│ Database Type   │ Strengths      │ Weaknesses     │ Use Cases      │
├─────────────────┼────────────────┼────────────────┼────────────────┤
│ PostgreSQL      │ ACID, SQL,     │ Scaling writes │ User data,     │
│                 │ Extensions     │ Complex shards │ Transactions   │
├─────────────────┼────────────────┼────────────────┼────────────────┤
│ MongoDB         │ Flexible       │ No joins,      │ Catalogs,      │
│                 │ schema, Scale  │ Consistency    │ CMS, Logs      │
├─────────────────┼────────────────┼────────────────┼────────────────┤
│ Cassandra       │ Write scale,   │ No joins,      │ Time-series,   │
│                 │ Availability   │ Limited query  │ IoT, Messages  │
├─────────────────┼────────────────┼────────────────┼────────────────┤
│ Redis           │ Speed,         │ Memory-bound,  │ Cache,         │
│                 │ Data structs   │ Persistence    │ Sessions       │
├─────────────────┼────────────────┼────────────────┼────────────────┤
│ Elasticsearch   │ Full-text      │ Not primary    │ Search,        │
│                 │ search, Scale  │ store, Cost    │ Logs, Metrics  │
└─────────────────┴────────────────┴────────────────┴────────────────┘
```

### 5.3 Schema Design Checklist

```
NORMALIZATION VS DENORMALIZATION
□ Normalize for write-heavy, consistency-critical
□ Denormalize for read-heavy, performance-critical
□ Consider read/write ratio

INDEXING
□ Index columns used in WHERE clauses
□ Index columns used in JOIN conditions
□ Index columns used in ORDER BY
□ Consider composite indexes for common queries
□ Avoid over-indexing (slows writes)

PARTITIONING/SHARDING
□ Choose partition key carefully (even distribution)
□ Avoid hot partitions
□ Consider access patterns
□ Plan for cross-partition queries

DATA TYPES
□ Use appropriate sizes (don't over-allocate)
□ Use native types when possible
□ Consider compression for large text/JSON
```

### 5.4 Consistency Patterns

```
STRONG CONSISTENCY
• All reads see latest write
• Use when: Financial, inventory, critical data
• Trade-off: Higher latency, lower availability

EVENTUAL CONSISTENCY
• Reads may see stale data temporarily
• Use when: Social feeds, analytics, caches
• Trade-off: May need conflict resolution

READ-YOUR-WRITES
• User sees their own writes immediately
• Others may see stale data
• Common compromise

CAUSAL CONSISTENCY
• Related operations seen in order
• Use when: Messaging, comments

CAP THEOREM REMINDER
• Consistency, Availability, Partition tolerance
• Can only guarantee 2 of 3 during partition
• CP: Strong consistency (banking)
• AP: High availability (social media)
```

---

## 6. High-Level Design Phase

### 6.1 Standard Components Checklist

```
CLIENT LAYER
□ Web clients (browsers)
□ Mobile apps (iOS, Android)
□ Third-party integrations
□ Internal tools

EDGE LAYER
□ CDN (static assets, caching)
□ DNS (load balancing, failover)
□ DDoS protection

GATEWAY LAYER
□ Load balancer (L4/L7)
□ API Gateway (routing, auth, rate limiting)
□ Reverse proxy

APPLICATION LAYER
□ Web servers
□ Application servers
□ Microservices

PROCESSING LAYER
□ Message queues
□ Stream processors
□ Background workers
□ Scheduled jobs

DATA LAYER
□ Primary database
□ Read replicas
□ Cache (Redis, Memcached)
□ Search index (Elasticsearch)
□ Object storage (S3)
□ Data warehouse

CROSS-CUTTING
□ Service discovery
□ Configuration management
□ Logging
□ Monitoring
□ Tracing
```

### 6.2 Architecture Patterns

```
MONOLITH
• Single deployable unit
• Good for: Starting out, small teams
• Trade-off: Scaling, deployment flexibility

MICROSERVICES
• Independent services, own databases
• Good for: Scale, team autonomy
• Trade-off: Complexity, network overhead

EVENT-DRIVEN
• Services communicate via events
• Good for: Decoupling, async processing
• Trade-off: Debugging, eventual consistency

CQRS (Command Query Responsibility Segregation)
• Separate read and write models
• Good for: Different read/write patterns
• Trade-off: Complexity, sync overhead

EVENT SOURCING
• Store events, not state
• Good for: Audit trails, temporal queries
• Trade-off: Complexity, storage
```

### 6.3 Component Diagram Template

```
                                    ┌─────────────┐
                                    │   Clients   │
                                    └──────┬──────┘
                                           │
                                    ┌──────▼──────┐
                                    │     CDN     │
                                    └──────┬──────┘
                                           │
                                    ┌──────▼──────┐
                                    │    Load     │
                                    │  Balancer   │
                                    └──────┬──────┘
                                           │
                                    ┌──────▼──────┐
                                    │ API Gateway │
                                    └──────┬──────┘
                                           │
        ┌──────────────────────────────────┼──────────────────────────────────┐
        │                                  │                                  │
 ┌──────▼──────┐                    ┌──────▼──────┐                    ┌──────▼──────┐
 │  Service A  │                    │  Service B  │                    │  Service C  │
 └──────┬──────┘                    └──────┬──────┘                    └──────┬──────┘
        │                                  │                                  │
        │                    ┌─────────────┴─────────────┐                    │
        │                    │                           │                    │
 ┌──────▼──────┐      ┌──────▼──────┐            ┌──────▼──────┐      ┌──────▼──────┐
 │  Database   │      │    Cache    │            │    Queue    │      │   Search    │
 │ (Primary)   │      │   (Redis)   │            │   (Kafka)   │      │   (ES)      │
 └──────┬──────┘      └─────────────┘            └──────┬──────┘      └─────────────┘
        │                                               │
 ┌──────▼──────┐                                 ┌──────▼──────┐
 │  Replicas   │                                 │   Workers   │
 └─────────────┘                                 └─────────────┘
```

---

## 7. Deep Dive Phase

### 7.1 Caching - Complete Checklist

```
WHAT TO CACHE
□ Database query results
□ Computed/aggregated data
□ Session data
□ User profiles
□ Configuration
□ API responses
□ HTML fragments
□ Static assets

CACHING PATTERNS
□ Cache-Aside (read: check cache → DB → update cache)
□ Read-Through (cache handles DB reads)
□ Write-Through (write to cache and DB together)
□ Write-Behind (write to cache, async to DB)
□ Refresh-Ahead (preemptively refresh expiring)

CACHE INVALIDATION
□ TTL-based (time-to-live)
□ Event-based (on write/update)
□ Version-based (cache key includes version)
□ Manual invalidation

EVICTION POLICIES
□ LRU (Least Recently Used) - most common
□ LFU (Least Frequently Used)
□ FIFO (First In First Out)
□ Random

CACHE ISSUES TO ADDRESS
□ Cache stampede (thundering herd)
□ Cache penetration (queries for non-existent)
□ Cache avalanche (mass expiration)
□ Hot keys
□ Cache consistency
```

### 7.2 Message Queues - Complete Checklist

```
WHEN TO USE QUEUES
□ Async processing
□ Decoupling services
□ Load leveling (absorb spikes)
□ Reliable delivery needed
□ Event-driven architecture

DELIVERY GUARANTEES
□ At-most-once (may lose messages)
□ At-least-once (may duplicate, most common)
□ Exactly-once (complex, rare)

QUEUE SELECTION
□ RabbitMQ: Complex routing, protocols
□ Kafka: High throughput, event streaming
□ SQS: Managed, simple
□ Redis Streams: When already using Redis

PATTERNS
□ Point-to-point (one consumer)
□ Pub/Sub (multiple consumers)
□ Fan-out (broadcast)
□ Work queue (load distribution)
□ Request-reply

CONSIDERATIONS
□ Message ordering requirements
□ Message size limits
□ Retention period
□ Dead letter queue for failures
□ Idempotency in consumers
```

### 7.3 Scaling - Complete Checklist

```
VERTICAL SCALING (Scale Up)
□ Bigger machines
□ More CPU, RAM, faster disk
□ Simpler but has limits
□ Single point of failure

HORIZONTAL SCALING (Scale Out)
□ More machines
□ Requires stateless design
□ Need load balancing
□ More complex but no ceiling

DATABASE SCALING
□ Read replicas (read scaling)
□ Sharding (write scaling)
□ Vertical partitioning (split tables)
□ Horizontal partitioning (split rows)

APPLICATION SCALING
□ Stateless services
□ Session externalization
□ Connection pooling
□ Async processing

SCALING TRIGGERS
□ CPU > 70% sustained
□ Memory > 80%
□ Request latency increasing
□ Error rate increasing
□ Queue depth growing
```

### 7.4 Load Balancing - Complete Checklist

```
ALGORITHMS
□ Round Robin (simple, equal distribution)
□ Weighted Round Robin (capacity-aware)
□ Least Connections (send to least busy)
□ IP Hash (sticky sessions)
□ Consistent Hashing (cache-friendly)
□ Random (surprisingly effective)

LAYER 4 VS LAYER 7
□ L4: TCP/UDP level, faster, less flexible
□ L7: HTTP level, content-aware routing

HEALTH CHECKS
□ TCP checks (port open)
□ HTTP checks (endpoint returns 200)
□ Application-level checks
□ Timeout and interval settings

CONSIDERATIONS
□ Session persistence needs
□ SSL termination location
□ Graceful draining during deploys
□ Geographic load balancing
```

### 7.5 Fault Tolerance - Complete Checklist

```
REDUNDANCY
□ No single points of failure
□ Multiple instances of each component
□ Multi-AZ deployment
□ Multi-region for critical systems

PATTERNS
□ Circuit Breaker (prevent cascade failures)
□ Retry with exponential backoff
□ Timeout (don't wait forever)
□ Bulkhead (isolate failures)
□ Fallback (graceful degradation)

FAILURE SCENARIOS TO CONSIDER
□ Server/instance failure
□ Network partition
□ Database failure
□ Downstream service failure
□ Cache failure
□ Queue failure
□ Region failure

GRACEFUL DEGRADATION
□ Serve stale cache data
□ Disable non-critical features
□ Queue requests for later
□ Return partial results
□ Show maintenance page
```

### 7.6 Security - Complete Checklist

```
AUTHENTICATION
□ Username/password + hashing (bcrypt)
□ Multi-factor authentication
□ OAuth 2.0 / OpenID Connect
□ API keys for services
□ JWT for stateless auth

AUTHORIZATION
□ Role-based access control (RBAC)
□ Attribute-based access control (ABAC)
□ Resource-based permissions
□ Principle of least privilege

DATA PROTECTION
□ Encryption at rest
□ Encryption in transit (TLS)
□ Key management
□ Data masking for sensitive fields
□ PII handling

API SECURITY
□ Rate limiting
□ Input validation
□ SQL injection prevention
□ XSS prevention
□ CORS configuration
□ Request signing

INFRASTRUCTURE
□ Network segmentation
□ Firewall rules
□ VPC and private subnets
□ Secret management
□ Regular security audits
```

### 7.7 Observability - Complete Checklist

```
LOGGING
□ Structured logging (JSON)
□ Correlation IDs across services
□ Appropriate log levels
□ Centralized log aggregation
□ Log retention policy

METRICS
□ Request rate
□ Error rate
□ Latency (p50, p95, p99)
□ Saturation (CPU, memory, disk)
□ Business metrics
□ Custom application metrics

TRACING
□ Distributed tracing
□ Span collection
□ Trace sampling strategy
□ Integration with logging

ALERTING
□ Define SLIs/SLOs
□ Alert on symptoms, not causes
□ Avoid alert fatigue
□ On-call rotation
□ Runbooks for common issues

DASHBOARDS
□ Service health overview
□ Key business metrics
□ Infrastructure metrics
□ Real-time and historical views
```

---

## 8. ML Systems Considerations

### 8.1 ML System Components

```
DATA LAYER
□ Data collection pipelines
□ Data validation
□ Feature store
□ Training data management
□ Data versioning

TRAINING LAYER
□ Experiment tracking
□ Model versioning
□ Hyperparameter tuning
□ Distributed training
□ GPU/TPU management

SERVING LAYER
□ Model deployment
□ Online vs batch inference
□ A/B testing
□ Shadow mode testing
□ Canary deployments

MONITORING LAYER
□ Data drift detection
□ Model performance monitoring
□ Prediction logging
□ Feedback loops
```

### 8.2 ML-Specific Trade-offs

```
ONLINE VS BATCH INFERENCE
□ Online: Real-time, higher infra cost, fresher
□ Batch: Periodic, cheaper, potentially stale

MODEL COMPLEXITY VS LATENCY
□ Complex model: Better accuracy, slower
□ Simple model: Faster, may sacrifice accuracy

FRESHNESS VS COST
□ Frequent retraining: Fresh, expensive
□ Infrequent retraining: Stale, cheaper

FEATURE COMPUTATION
□ Pre-computed: Fast serving, stale features
□ Real-time: Fresh, higher latency
```

### 8.3 ML Questions to Ask

```
□ What is the prediction latency requirement?
□ How often does the model need to be retrained?
□ What is the training data volume?
□ What features are needed (real-time vs batch)?
□ How to handle model failures?
□ How to measure model performance in production?
□ How to handle feedback loops?
□ A/B testing requirements?
```

---

## 9. Trade-offs Master List

### 9.1 Fundamental Trade-offs

```
CONSISTENCY vs AVAILABILITY
• Strong consistency reduces availability
• High availability requires relaxed consistency
• Choose based on data criticality

LATENCY vs THROUGHPUT
• Optimizing for one may hurt the other
• Batching improves throughput, hurts latency
• Caching helps both but adds complexity

SIMPLICITY vs FLEXIBILITY
• Simple solutions are easier to maintain
• Flexible solutions handle more cases
• Start simple, add flexibility when needed

COST vs PERFORMANCE
• Better performance usually costs more
• Find the knee of the cost/performance curve
• Consider total cost of ownership

CONSISTENCY vs LATENCY (PACELC)
• When Partitioned: Availability vs Consistency
• Else: Latency vs Consistency

STORAGE vs COMPUTATION
• Store pre-computed results (fast read, more storage)
• Compute on demand (less storage, slower read)
```

### 9.2 Component-Specific Trade-offs

```
SQL vs NoSQL
□ SQL: ACID, joins, mature → Schema rigidity, scaling complexity
□ NoSQL: Flexible, scales → No joins, eventual consistency

Synchronous vs Asynchronous
□ Sync: Simple, immediate feedback → Blocking, tight coupling
□ Async: Decoupled, resilient → Complexity, eventual consistency

Push vs Pull
□ Push: Real-time, immediate → Connection overhead, complexity
□ Pull: Simple, client-controlled → Latency, polling overhead

Monolith vs Microservices
□ Monolith: Simple, fast dev → Scaling limits, deployment coupling
□ Microservices: Scale, autonomy → Complexity, network overhead

Cache-Aside vs Read-Through
□ Cache-Aside: Control, flexibility → More code, consistency risk
□ Read-Through: Simpler code → Less control, cache dependency

Fan-out on Write vs Fan-out on Read
□ On Write: Fast reads → Write amplification, storage cost
□ On Read: Storage efficient → Slower reads, compute cost
```

---

## 10. Heuristics & Rules of Thumb

### 10.1 Numbers Every Developer Should Know

```
LATENCY
• L1 cache: 1 ns
• L2 cache: 4 ns
• RAM: 100 ns
• SSD random read: 16 μs
• HDD seek: 2 ms
• Round trip same datacenter: 500 μs
• Round trip cross-country: 30-100 ms

THROUGHPUT
• SSD: 500 MB/s
• 1 Gbps network: 125 MB/s
• HDD: 100 MB/s

AVAILABILITY
• 99.9% = 8.77 hours downtime/year
• 99.99% = 52.6 minutes/year
• 99.999% = 5.26 minutes/year
```

### 10.2 Capacity Quick Reference

```
SINGLE SERVER LIMITS (rough)
• Web server: 10K-50K concurrent connections
• Database: 10K-100K QPS (depends on query)
• Redis: 100K ops/sec
• Kafka: 100K-1M messages/sec

STORAGE QUICK MATH
• 1 KB × 1M = 1 GB
• 1 MB × 1M = 1 TB
• 1 GB × 1M = 1 PB

TRAFFIC QUICK MATH
• 1M requests/day ≈ 12 QPS
• 10M requests/day ≈ 120 QPS
• 100M requests/day ≈ 1,200 QPS
• 1B requests/day ≈ 12,000 QPS
```

### 10.3 Design Heuristics

```
80/20 RULE
• 80% of traffic goes to 20% of data
• Cache the hot 20%

3-SECOND RULE
• Users abandon if page takes > 3 seconds
• Optimize critical path

5-9s RULE
• 5 nines (99.999%) availability is very hard
• Most systems target 3-4 nines

READ:WRITE RATIO
• Social media: 100:1 to 1000:1 (very read-heavy)
• Messaging: 1:1 to 10:1
• Logging: 1:100+ (very write-heavy)

REPLICATION
• 3 copies is standard for durability
• 5+ for critical data

DATA GROWTH
• Plan for 10x current size
• Re-evaluate architecture at 10x
```

---

## 11. Mental Models

### 11.1 System Design Mental Models

```
SEPARATION OF CONCERNS
• Each component does one thing well
• Easier to understand, test, scale

DEFENSE IN DEPTH
• Multiple layers of protection
• No single point of failure

IDEMPOTENCY
• Same operation, same result
• Critical for retries and at-least-once

EVENTUAL CONSISTENCY
• System will converge to consistent state
• Acceptable for many use cases

BACK-OF-ENVELOPE
• Quick estimates to validate approach
• Don't need exact numbers

GRACEFUL DEGRADATION
• Fail partially, not completely
• Serve stale data over nothing

BLAST RADIUS
• Limit impact of failures
• Bulkheads, circuit breakers

CAP THEOREM THINKING
• During partition, choose C or A
• Understand your system's choice
```

### 11.2 Problem-Solving Mental Models

```
START WITH WHY
• Understand the problem before solving
• Requirements drive design

TOP-DOWN DECOMPOSITION
• Start high-level, drill into details
• Avoid premature optimization

BOTTLENECK THINKING
• System is as fast as slowest component
• Identify and address bottlenecks

TRADE-OFF ARTICULATION
• Every decision has pros and cons
• Make trade-offs explicit

FAILURE MODE ANALYSIS
• What can go wrong?
• How do we detect and recover?

SCALING DIMENSIONS
• Users, data, geography, features
• Consider each dimension
```

---

## 12. Common Mistakes to Avoid

### 12.1 Requirements Phase

```
❌ Jumping into design without clarifying requirements
❌ Not asking about scale expectations
❌ Ignoring non-functional requirements
❌ Trying to solve everything (not scoping)
❌ Not considering edge cases
```

### 12.2 Design Phase

```
❌ Over-engineering from the start
❌ Choosing technology without justification
❌ Ignoring failure scenarios
❌ Not discussing trade-offs
❌ Single point of failure in design
❌ Designing without considering operations
```

### 12.3 Communication

```
❌ Not drawing diagrams
❌ Going too deep too early
❌ Not driving the conversation
❌ Not validating understanding with interviewer
❌ Giving one-word answers without explanation
```

### 12.4 Technical Mistakes

```
❌ Using wrong database for access pattern
❌ Not considering consistency requirements
❌ Ignoring caching opportunities
❌ Synchronous calls where async would work
❌ Not planning for horizontal scaling
❌ Forgetting about data growth
```

---

## Quick Reference Card

```
┌────────────────────────────────────────────────────────────────────┐
│                    SYSTEM DESIGN QUICK REFERENCE                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PHASE 1: REQUIREMENTS (5 min)                                     │
│  ✓ Users: Who? How many?                                           │
│  ✓ Features: Core 2-3 use cases?                                   │
│  ✓ Scale: DAU? Growth?                                             │
│  ✓ NFRs: Latency? Availability? Consistency?                       │
│                                                                     │
│  PHASE 2: ESTIMATION (5 min)                                       │
│  ✓ QPS = Daily requests / 86,400                                   │
│  ✓ Storage = Users × data × retention × 3                          │
│  ✓ Bandwidth = Size × QPS                                          │
│                                                                     │
│  PHASE 3: API (5 min)                                              │
│  ✓ 3-5 core endpoints                                              │
│  ✓ Protocol choice (REST/gRPC/WebSocket)                           │
│  ✓ Auth approach                                                   │
│                                                                     │
│  PHASE 4: HIGH-LEVEL (10 min)                                      │
│  ✓ Draw diagram                                                    │
│  ✓ Client → LB → API → Services → Data                            │
│  ✓ Show data flow                                                  │
│                                                                     │
│  PHASE 5: DEEP DIVE (15 min)                                       │
│  ✓ Database choice + schema                                        │
│  ✓ Caching strategy                                                │
│  ✓ Scaling approach                                                │
│  ✓ Failure handling                                                │
│                                                                     │
│  PHASE 6: WRAP-UP (5 min)                                          │
│  ✓ Key trade-offs                                                  │
│  ✓ Bottlenecks                                                     │
│  ✓ Improvements                                                    │
│                                                                     │
├────────────────────────────────────────────────────────────────────┤
│  KEY QUESTIONS TO ALWAYS ASK                                        │
│  • What's the read/write ratio?                                    │
│  • What's the consistency requirement?                             │
│  • What's the latency requirement?                                 │
│  • What's the availability requirement?                            │
│  • What's the expected scale and growth?                           │
├────────────────────────────────────────────────────────────────────┤
│  KEY TRADE-OFFS TO ALWAYS MENTION                                   │
│  • Consistency vs Availability                                     │
│  • Latency vs Throughput                                           │
│  • Simplicity vs Flexibility                                       │
│  • Cost vs Performance                                             │
└────────────────────────────────────────────────────────────────────┘
```

---

*Use this template as your go-to reference for any system design problem. For detailed explanations, refer to the individual section files.*
