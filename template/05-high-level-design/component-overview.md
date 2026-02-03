# System Components Overview

A comprehensive guide to the building blocks of modern distributed systems.

---

## Standard Architecture Template

```
                              ┌─────────────────────────────────────┐
                              │            CLIENTS                  │
                              │    (Web, Mobile, IoT, Third-party)  │
                              └──────────────────┬──────────────────┘
                                                 │
                                                 ▼
                              ┌─────────────────────────────────────┐
                              │              CDN                     │
                              │   (CloudFront, Cloudflare, Akamai)  │
                              └──────────────────┬──────────────────┘
                                                 │
                                                 ▼
                              ┌─────────────────────────────────────┐
                              │         LOAD BALANCER               │
                              │      (ALB, NGINX, HAProxy)          │
                              └──────────────────┬──────────────────┘
                                                 │
                                                 ▼
                              ┌─────────────────────────────────────┐
                              │          API GATEWAY                │
                              │  (Kong, AWS API Gateway, Envoy)     │
                              └──────────────────┬──────────────────┘
                                                 │
              ┌──────────────────────────────────┼──────────────────────────────────┐
              │                                  │                                  │
              ▼                                  ▼                                  ▼
┌─────────────────────────┐    ┌─────────────────────────┐    ┌─────────────────────────┐
│      SERVICE A          │    │      SERVICE B          │    │      SERVICE C          │
│   (Microservice)        │    │   (Microservice)        │    │   (Microservice)        │
└───────────┬─────────────┘    └───────────┬─────────────┘    └───────────┬─────────────┘
            │                              │                              │
            └──────────────────────────────┼──────────────────────────────┘
                                           │
     ┌─────────────────────────────────────┼─────────────────────────────────────┐
     │                                     │                                     │
     ▼                                     ▼                                     ▼
┌──────────────┐                   ┌──────────────┐                   ┌──────────────┐
│    CACHE     │                   │   DATABASE   │                   │MESSAGE QUEUE │
│   (Redis)    │                   │ (PostgreSQL) │                   │   (Kafka)    │
└──────────────┘                   └──────────────┘                   └──────┬───────┘
                                                                              │
                                                                              ▼
                                                                   ┌──────────────────┐
                                                                   │     WORKERS      │
                                                                   │(Background Jobs) │
                                                                   └──────────────────┘
```

---

## 1. Content Delivery Network (CDN)

### What It Does
```
- Caches static content at edge locations globally
- Reduces latency by serving content from nearest location
- Offloads traffic from origin servers
- Provides DDoS protection
```

### What to Cache
```
✓ Static assets (JS, CSS, images, fonts)
✓ Media files (videos, audio)
✓ Static HTML pages
✓ API responses (if appropriate)

✗ Personalized content
✗ Real-time data
✗ Authenticated content (usually)
```

### Key Concepts
```
TTL (Time-To-Live):
  - How long content is cached
  - Trade-off: Freshness vs. cache hit ratio

Cache Invalidation:
  - Purge by URL
  - Purge by tag/surrogate key
  - Versioned URLs (main.v123.js)

Origin Shield:
  - Intermediate cache between edge and origin
  - Reduces origin load for cache misses
```

### CDN Providers
```
Provider     │ Strength                    │ Use Case
─────────────┼─────────────────────────────┼─────────────────
CloudFront   │ AWS integration             │ AWS-based systems
Cloudflare   │ Security, DDoS protection   │ Security-focused
Akamai       │ Enterprise, global reach    │ Large enterprises
Fastly       │ Real-time purging           │ Dynamic content
```

---

## 2. Load Balancer

### Types
```
Layer 4 (Transport):
  - Routes based on IP and port
  - Faster, less intelligent
  - No content inspection
  - Examples: NLB, HAProxy (TCP mode)

Layer 7 (Application):
  - Routes based on content (URL, headers)
  - More flexible routing
  - SSL termination
  - Examples: ALB, NGINX, HAProxy (HTTP mode)
```

### Load Balancing Algorithms
```
Algorithm              │ Description                  │ When to Use
───────────────────────┼──────────────────────────────┼─────────────────
Round Robin            │ Sequential distribution      │ Uniform servers
Weighted Round Robin   │ Based on server capacity     │ Mixed capacity
Least Connections      │ To server with fewest conns  │ Variable load
IP Hash                │ Same client → same server    │ Session affinity
Consistent Hashing     │ Minimizes redistribution     │ Caching, stateful
```

### Health Checks
```
Types:
  - HTTP health check (GET /health → 200)
  - TCP health check (port open)
  - Custom health checks

Configuration:
  - Interval: How often to check (5-30 seconds)
  - Threshold: Failures before unhealthy (2-3)
  - Timeout: Max wait for response (5 seconds)
```

### Key Features
```
SSL Termination:
  - Decrypt HTTPS at load balancer
  - Forward HTTP to backend
  - Offloads CPU from services

Connection Draining:
  - Gracefully remove server from rotation
  - Complete in-flight requests
  - Essential for zero-downtime deploys

Sticky Sessions:
  - Route user to same backend
  - Use when state is server-local
  - Better: Externalize state (Redis)
```

---

## 3. API Gateway

### Responsibilities
```
┌────────────────────────────────────────────────────────────────┐
│                        API GATEWAY                              │
├────────────────────────────────────────────────────────────────┤
│  Authentication       │ Verify tokens, API keys                │
│  Rate Limiting        │ Throttle requests per user/IP          │
│  Request Routing      │ Route to appropriate service           │
│  Request Transform    │ Modify headers, body                   │
│  Response Transform   │ Aggregate, format responses            │
│  Caching              │ Cache common responses                 │
│  Logging/Monitoring   │ Centralized request logging            │
│  Circuit Breaking     │ Prevent cascade failures               │
└────────────────────────────────────────────────────────────────┘
```

### Gateway Patterns
```
1. Edge Gateway (External API):
   Internet → Gateway → Internal Services

   Purpose: Single entry point for all external traffic
   - Handles public API requests
   - Performs authentication/authorization
   - Rate limiting per client/API key
   - SSL termination
   - Request routing to appropriate microservices

   Use When:
   - Building public-facing APIs
   - Need centralized security and monitoring
   - Want to hide internal architecture from clients

   Example: All external clients hit api.company.com which routes
   to order-service, user-service, payment-service internally

2. Internal Gateway (Service Mesh):
   Service A → Gateway → Service B

   Purpose: Manage service-to-service communication
   - Service discovery and load balancing
   - Circuit breaking and retries
   - Mutual TLS between services
   - Observability (tracing, metrics)
   - Traffic shaping and canary deployments

   Use When:
   - Many microservices communicating
   - Need resilience patterns (circuit breakers)
   - Require service-level security and monitoring

   Example: Order service calls payment service through mesh,
   which handles retries, timeouts, and load balancing automatically

3. Backend for Frontend (BFF):
   Web App  → Web Gateway  → Services
   Mobile   → Mobile Gateway → Services

   Purpose: Dedicated gateway per client type
   - Aggregates multiple service calls into one
   - Transforms data for specific client needs
   - Optimizes payload size (mobile gets smaller responses)
   - Different authentication flows per platform
   - Client-specific caching strategies

   Use When:
   - Web and mobile have different data needs
   - Want to avoid "fat" APIs with unused fields
   - Each platform has unique requirements
   - Need to optimize for bandwidth/latency per client

   Example: Mobile BFF returns thumbnail images and paginated data,
   while Web BFF returns full images and larger data sets
```

### API Gateway Options
```
Solution         │ Type            │ Best For
─────────────────┼─────────────────┼───────────────────────
Kong             │ Open-source     │ Kubernetes, flexibility
AWS API Gateway  │ Managed         │ AWS serverless
Envoy            │ Proxy/Mesh      │ Service mesh
NGINX Plus       │ Commercial      │ High performance
Apigee           │ Enterprise      │ API management
```

---

## 4. Application Servers

### Design Principles
```
Stateless:
  - No local state (sessions, cache)
  - State in external stores (Redis, DB)
  - Easy horizontal scaling
  - Any server can handle any request

Horizontal Scaling:
  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ Server 1 │  │ Server 2 │  │ Server 3 │
  └──────────┘  └──────────┘  └──────────┘
       │             │             │
       └─────────────┼─────────────┘
                     │
              ┌──────▼──────┐
              │   Shared    │
              │   State     │
              │  (Redis)    │
              └─────────────┘
```

### Scaling Strategies
```
Horizontal (Scale Out):
  - Add more servers
  - Preferred for most workloads
  - Limit: Stateless design required

Vertical (Scale Up):
  - Bigger server (more CPU/RAM)
  - Simpler but has limits
  - Use for: Databases, some workloads

Auto-scaling:
  - Scale based on metrics (CPU, requests)
  - Scale-out: Add instances
  - Scale-in: Remove instances
  - Configure: Min, max, target metric
```

### Container Orchestration
```
Kubernetes Concepts:
  - Pod: One or more containers
  - Deployment: Desired state definition
  - Service: Stable network endpoint
  - Ingress: External access

Scaling in K8s:
  - Horizontal Pod Autoscaler (HPA)
  - Vertical Pod Autoscaler (VPA)
  - Cluster Autoscaler
```

---

## 5. Caching Layer

### Cache Placement
```
┌──────────────────────────────────────────────────────────────────┐
│                      CACHING LAYERS                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. Browser Cache         │  Client-side, limited control         │
│         ↓                 │                                       │
│  2. CDN Cache             │  Edge, static content                 │
│         ↓                 │                                       │
│  3. API Gateway Cache     │  Response caching                     │
│         ↓                 │                                       │
│  4. Application Cache     │  In-memory (local)                    │
│         ↓                 │                                       │
│  5. Distributed Cache     │  Redis, Memcached                     │
│         ↓                 │                                       │
│  6. Database Cache        │  Query cache, buffer pool             │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Cache Strategies
```
Cache-Aside (Lazy Loading):
  1. Check cache
  2. If miss, query database
  3. Store in cache
  4. Return to caller

Write-Through:
  1. Write to cache AND database
  2. Ensures consistency
  3. Higher write latency

Write-Behind (Write-Back):
  1. Write to cache only
  2. Async write to database
  3. Risk: Data loss if cache fails
```

### When to Cache
```
✓ Read-heavy data
✓ Expensive computations
✓ Slow database queries
✓ External API responses
✓ Session data

✗ Rapidly changing data
✗ Data requiring strong consistency
✗ Large objects (unless CDN)
✗ Rarely accessed data
```

---

## 6. Database Layer

### Database Tiers
```
Primary Database:
  - Handles writes
  - Source of truth
  - ACID transactions

Read Replicas:
  - Handle read queries
  - Async replication from primary
  - Scale read capacity

Cache Layer:
  - Hot data in memory
  - Sub-millisecond access
  - Reduce database load
```

### Data Partitioning
```
                    ┌───────────────┐
                    │    Router     │
                    └───────┬───────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
   ┌─────────┐         ┌─────────┐         ┌─────────┐
   │ Shard 1 │         │ Shard 2 │         │ Shard 3 │
   │ A - H   │         │ I - P   │         │ Q - Z   │
   └─────────┘         └─────────┘         └─────────┘

Shard by:
  - User ID (even distribution)
  - Tenant ID (multi-tenant)
  - Geographic region
  - Time range (time-series)
```

---

## 7. Message Queue

### When to Use
```
✓ Async processing (email, notifications)
✓ Workload leveling (absorb spikes)
✓ Service decoupling
✓ Reliable delivery needed
✓ Event-driven architecture

✗ Synchronous request-response
✗ Simple direct communication
✗ Sub-millisecond latency required
```

### Queue Patterns
```
Point-to-Point:
  Producer → Queue → Consumer
  - Each message processed once
  - Work distribution

Pub/Sub:
  Publisher → Topic → Multiple Subscribers
  - Broadcast messages
  - Event notification

Dead Letter Queue:
  - Failed messages stored separately
  - Debugging and recovery
  - Prevents blocking
```

### Message Queue Options
```
Technology    │ Model          │ Best For
──────────────┼────────────────┼────────────────────────
Kafka         │ Log-based      │ Event streaming, high throughput
RabbitMQ      │ Traditional    │ Complex routing, reliability
SQS           │ Managed queue  │ AWS, simple async
Redis Streams │ In-memory      │ Real-time, simple needs
```

---

## 8. Background Workers

### Worker Types
```
Queue Workers:
  - Process messages from queue
  - Horizontal scaling
  - Retry on failure

Scheduled Jobs (Cron):
  - Run at specific times
  - Daily reports, cleanup
  - Single execution (leader election)

Event Processors:
  - React to events
  - Stream processing
  - Real-time analytics
```

### Worker Design Patterns
```
Idempotency:
  - Same message processed multiple times = same result
  - Essential for at-least-once delivery
  - Use idempotency keys

Retry Strategy:
  - Exponential backoff
  - Max retry count
  - Dead letter after failures

Visibility Timeout:
  - Message hidden while processing
  - Re-appears if not acknowledged
  - Prevents duplicate processing
```

---

## 9. Object Storage

### When to Use
```
✓ Large files (images, videos, documents)
✓ Backup and archival
✓ Static website hosting
✓ Data lake storage

✗ Structured data (use database)
✗ Frequently updated files
✗ Low-latency access needed
```

### Storage Tiers
```
Tier              │ Access Pattern      │ Cost    │ Latency
──────────────────┼─────────────────────┼─────────┼──────────
Standard          │ Frequent access     │ Higher  │ Milliseconds
Infrequent Access │ Monthly access      │ Medium  │ Milliseconds
Glacier/Archive   │ Yearly access       │ Lowest  │ Hours
```

### Best Practices
```
Naming:
  - Use prefixes for partitioning
  - Avoid sequential names (hot spots)
  - Good: user-123/photos/2024/01/image.jpg

Security:
  - Private by default
  - Pre-signed URLs for temporary access
  - Bucket policies and IAM
```

---

## Component Selection Checklist

```
For each component, consider:

□ Throughput requirements
□ Latency requirements
□ Availability requirements
□ Consistency requirements
□ Cost constraints
□ Operational complexity
□ Team expertise
□ Vendor lock-in
□ Scaling needs
□ Security requirements
```

---

## Next Steps

1. → [Architecture Diagrams](architecture-diagrams.md) - Template diagrams
2. → [Design Checklist](design-checklist.md) - Comprehensive checklist
3. → [Deep Dive](../06-deep-dive/) - Detailed component guides
