# Scaling Decision Framework

Structured approach to scaling systems effectively.

---

## Scaling Decision Tree

```
                        Performance Issue
                              │
                              ▼
                  ┌───────────────────────┐
                  │ Identify the bottleneck│
                  └───────────┬───────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │   CPU   │          │ Memory  │          │   I/O   │
   └────┬────┘          └────┬────┘          └────┬────┘
        │                    │                    │
        ▼                    ▼                    ▼
  Optimize code         Add caching          Optimize queries
  Add servers           Larger instance      Add indexes
  Use async             Distribute data      Add replicas
                                             Use SSD
```

---

## Horizontal vs Vertical Scaling

### Vertical Scaling (Scale Up)

```
Before:                 After:
┌──────────┐           ┌──────────────┐
│ 4 CPU    │    →      │ 16 CPU       │
│ 16GB RAM │           │ 64GB RAM     │
│ 500GB SSD│           │ 2TB SSD      │
└──────────┘           └──────────────┘

When to use:
  ✓ Quick fix needed
  ✓ Application isn't designed for distribution
  ✓ Database with complex queries
  ✓ Single-threaded bottlenecks

Limits:
  ✗ Hardware limits exist
  ✗ Expensive at high end
  ✗ Single point of failure
  ✗ Downtime during upgrade
```

### Horizontal Scaling (Scale Out)

```
Before:                 After:
┌──────────┐           ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Server 1 │    →      │ Server 1 │ │ Server 2 │ │ Server 3 │
└──────────┘           └──────────┘ └──────────┘ └──────────┘

When to use:
  ✓ Need unlimited scaling
  ✓ Stateless services
  ✓ Traffic is variable
  ✓ High availability required

Requirements:
  • Stateless design
  • Load balancer
  • Shared storage for state
  • Service discovery
```

---

## Scaling By Component

### Application Servers

```
Problem: High CPU utilization, slow response

Solutions (in order):
  1. Code optimization
     - Profile and fix hotspots
     - Efficient algorithms

  2. Horizontal scaling
     - Add more instances
     - Auto-scaling based on CPU/requests

  3. Async processing
     - Move non-critical work to queues
     - Reduce request latency

Decision factors:
  • Stateless? → Horizontal scaling easy
  • CPU bound? → More instances
  • I/O bound? → Async processing
```

### Database

```
Problem: High latency, connection limits

Read Scaling:
  1. Add caching layer (Redis)
  2. Add read replicas
  3. Denormalize hot paths

Write Scaling:
  1. Optimize queries and indexes
  2. Use write-behind cache
  3. Implement sharding

Decision tree:
  Read-heavy (>90% reads)?
    → Read replicas + caching

  Write-heavy?
    → Sharding + async writes

  Both?
    → CQRS (separate read/write stores)
```

### Cache

```
Problem: Cache misses, memory limits

Solutions:
  1. Increase cache size
  2. Optimize cache keys
  3. Use distributed cache (Redis Cluster)
  4. Multi-tier caching

Decision factors:
  • Hit ratio < 90%? → Increase size or TTL
  • Single node limit? → Use cluster
  • Hot keys? → Local cache + distributed cache
```

### Message Queue

```
Problem: Growing backlog, high latency

Solutions:
  1. Add more consumers
  2. Optimize consumer processing
  3. Partition for parallelism
  4. Use larger instance

Decision factors:
  • Consumer slow? → Optimize or batch
  • Not enough consumers? → Scale horizontally
  • Ordering required? → Partition by key
```

---

## Auto-Scaling Strategies

### Metric-Based Scaling

```
Scale based on metrics:

CPU-based:
  Scale out: CPU > 70% for 5 minutes
  Scale in: CPU < 30% for 10 minutes

Request-based:
  Scale out: RPS > threshold
  Scale in: RPS < threshold

Queue-based:
  Scale out: Queue depth > 1000
  Scale in: Queue depth < 100

Custom metrics:
  Scale based on business metrics
  Example: Active users, orders/minute
```

### Predictive Scaling

```
Scale before demand:
  - Learn traffic patterns
  - Pre-scale for known events
  - Avoid cold start latency

Example:
  Historical pattern shows 2x traffic at 9 AM
  → Pre-scale at 8:45 AM

Tools:
  - AWS Predictive Scaling
  - Custom ML models
```

### Scaling Configuration

```
Key parameters:
  min_instances: 2        # Minimum for availability
  max_instances: 100      # Cost limit
  scale_out_cooldown: 60s # Prevent flapping
  scale_in_cooldown: 300s # Conservative scale-in
  target_metric: 70%      # Target utilization
```

---

## Scaling Patterns

### Pattern 1: Stateless Services

```
┌─────────────┐
│    Load     │
│  Balancer   │
└──────┬──────┘
       │
  ┌────┼────┐
  │    │    │
  ▼    ▼    ▼
┌───┐ ┌───┐ ┌───┐
│ S │ │ S │ │ S │  ← Stateless (easy to add/remove)
└───┘ └───┘ └───┘
  │    │    │
  └────┼────┘
       │
  ┌────▼────┐
  │  Shared │
  │  State  │
  │ (Redis) │
  └─────────┘

Key: Externalize all state
```

### Pattern 2: Data Partitioning

```
┌─────────────────────────────────────────────────┐
│                    Router                        │
└───────────────────────┬─────────────────────────┘
                        │
     ┌──────────────────┼──────────────────┐
     │                  │                  │
     ▼                  ▼                  ▼
┌─────────┐       ┌─────────┐       ┌─────────┐
│ Shard 1 │       │ Shard 2 │       │ Shard 3 │
│ A-H     │       │ I-P     │       │ Q-Z     │
└─────────┘       └─────────┘       └─────────┘

Key: Partition data by key to distribute load
```

### Pattern 3: Read Replicas

```
         ┌─────────────────────────────────────┐
         │              Writes                  │
         │                │                     │
         │          ┌─────▼─────┐               │
         │          │  Primary  │               │
         │          └─────┬─────┘               │
         │                │ Replication         │
         │     ┌──────────┼──────────┐         │
         │     │          │          │         │
         │ ┌───▼───┐  ┌───▼───┐  ┌───▼───┐    │
         │ │Replica│  │Replica│  │Replica│    │
         │ └───────┘  └───────┘  └───────┘    │
         │     │          │          │         │
         │     └──────────┼──────────┘         │
         │                │                     │
         │              Reads                   │
         └─────────────────────────────────────┘

Key: Separate read and write paths
```

### Pattern 4: CQRS

```
┌────────────────────────────────────────────────────────┐
│                        Commands                         │
│                           │                             │
│                    ┌──────▼──────┐                     │
│                    │   Write     │                     │
│                    │   Service   │                     │
│                    └──────┬──────┘                     │
│                           │                             │
│                    ┌──────▼──────┐                     │
│                    │  Write DB   │                     │
│                    │  (OLTP)     │                     │
│                    └──────┬──────┘                     │
│                           │ Events                     │
│                    ┌──────▼──────┐                     │
│                    │   Read DB   │                     │
│                    │  (OLAP)     │                     │
│                    └──────┬──────┘                     │
│                           │                             │
│                    ┌──────▼──────┐                     │
│                    │    Read     │                     │
│                    │   Service   │                     │
│                    └─────────────┘                     │
│                                                         │
│                        Queries                          │
└────────────────────────────────────────────────────────┘

Key: Optimize separately for reads and writes
```

---

## Scaling Decision Checklist

```
Before scaling:

□ Identified actual bottleneck (not guessing)
□ Optimized code/queries first
□ Added appropriate caching
□ Considered cost implications
□ Planned for failure during scaling
□ Tested scaling approach
□ Set up monitoring for new scale
□ Documented the change
```

---

## Anti-Patterns to Avoid

```
1. Premature Scaling
   ✗ Scaling before knowing bottleneck
   ✓ Measure first, scale based on data

2. Ignoring the Easy Wins
   ✗ Adding servers before adding indexes
   ✓ Optimize before scaling

3. Scaling Everything
   ✗ Scaling all services uniformly
   ✓ Scale the bottleneck

4. No Scale-In Strategy
   ✗ Only scaling out
   ✓ Plan for scaling in to save costs

5. Tight Coupling
   ✗ Services dependent on specific instances
   ✓ Loose coupling, service discovery
```

---

## Next Steps

1. → [Database Decisions](database-decisions.md) - Database scaling
2. → [Caching Decisions](caching-decisions.md) - Cache scaling
3. → [Case Studies](../10-case-studies/) - See scaling in practice
