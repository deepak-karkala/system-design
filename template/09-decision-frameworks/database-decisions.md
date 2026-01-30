# Database Decision Framework

Structured approach to selecting and designing databases for your system.

---

## Database Selection Decision Tree

```
                            START
                              │
                              ▼
                 ┌─────────────────────────┐
                 │ Need ACID transactions? │
                 └───────────┬─────────────┘
                             │
              ┌──────────────┴──────────────┐
              │ Yes                         │ No
              ▼                             ▼
     ┌────────────────┐          ┌─────────────────────┐
     │ SQL Database   │          │ Schema flexibility? │
     │ (PostgreSQL,   │          └──────────┬──────────┘
     │  MySQL)        │                     │
     └────────────────┘       ┌─────────────┴─────────────┐
                              │ Yes                       │ No
                              ▼                           ▼
                   ┌─────────────────┐       ┌───────────────────────┐
                   │ Document DB     │       │ Simple key-value?     │
                   │ (MongoDB)       │       └───────────┬───────────┘
                   └─────────────────┘                   │
                                            ┌────────────┴────────────┐
                                            │ Yes                     │ No
                                            ▼                         ▼
                                 ┌──────────────────┐    ┌───────────────────┐
                                 │ Key-Value Store  │    │ Write-heavy?      │
                                 │ (Redis, DynamoDB)│    └─────────┬─────────┘
                                 └──────────────────┘              │
                                                        ┌──────────┴──────────┐
                                                        │ Yes                 │ No
                                                        ▼                     ▼
                                             ┌──────────────────┐   ┌───────────────┐
                                             │ Wide Column      │   │ Consider SQL  │
                                             │ (Cassandra)      │   │ or Document   │
                                             └──────────────────┘   └───────────────┘
```

---

## Key Questions to Ask

### 1. Data Model Questions

```
Q: What are the main entities and their relationships?
   → Many-to-many relationships → SQL
   → Nested/hierarchical data → Document DB
   → Simple key-based access → Key-Value

Q: How complex are the queries?
   → Complex joins and aggregations → SQL
   → Document-level queries → Document DB
   → Simple lookups → Key-Value

Q: How often does the schema change?
   → Rarely, well-defined → SQL
   → Frequently evolving → Document DB
   → Schema-less → Key-Value
```

### 2. Scale Questions

```
Q: What's the data volume?
   → < 1TB → Single SQL node likely sufficient
   → 1-100 TB → Consider sharding or NoSQL
   → > 100 TB → Distributed systems (Cassandra, BigQuery)

Q: What's the read/write ratio?
   → Read-heavy (100:1) → SQL with replicas, heavy caching
   → Write-heavy (1:10) → Cassandra, time-series DB
   → Balanced → Depends on other factors

Q: What's the QPS requirement?
   → < 10K QPS → Most databases work
   → 10K-100K QPS → Need caching, read replicas
   → > 100K QPS → Sharding, distributed systems
```

### 3. Consistency Questions

```
Q: Is strong consistency required?
   → Financial transactions → Yes → SQL
   → Social media feeds → No → Eventually consistent OK

Q: What happens if users see stale data?
   → Unacceptable (banking) → Strong consistency
   → Acceptable (like counts) → Eventual consistency

Q: Cross-region requirements?
   → Single region → SQL can work
   → Multi-region → Consider eventually consistent systems
```

---

## Database Comparison Matrix

```
┌─────────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ Factor          │ PostgreSQL  │ MongoDB     │ Cassandra   │ Redis       │
├─────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ Data Model      │ Relational  │ Document    │ Wide Column │ Key-Value   │
│ Consistency     │ Strong      │ Configurable│ Tunable     │ Strong*     │
│ Scaling         │ Vertical    │ Horizontal  │ Horizontal  │ Cluster     │
│ Joins           │ Native      │ Limited     │ None        │ None        │
│ Transactions    │ Full ACID   │ Limited     │ Limited     │ Limited     │
│ Query Language  │ SQL         │ MQL         │ CQL         │ Commands    │
│ Best For        │ Complex     │ Flexible    │ Write-heavy │ Caching,    │
│                 │ queries     │ schema      │ time-series │ sessions    │
└─────────────────┴─────────────┴─────────────┴─────────────┴─────────────┘

* Redis cluster has eventual consistency
```

---

## Use Case Quick Reference

```
Use Case                    → Database Choice
─────────────────────────────────────────────────────────
User accounts, profiles     → SQL (PostgreSQL)
Financial transactions      → SQL (PostgreSQL with strong isolation)
Product catalog             → Document DB (MongoDB)
Shopping cart               → Key-Value (Redis)
Session storage             → Key-Value (Redis)
Analytics events            → Wide Column (Cassandra) or Time-Series
Search                      → Elasticsearch (secondary)
Caching                     → Redis, Memcached
Time-series metrics         → InfluxDB, TimescaleDB
Graph relationships         → Neo4j
Logs                        → Elasticsearch, Cassandra
Real-time messaging         → Redis, Cassandra
```

---

## Multi-Database Architecture

```
Many systems use multiple databases:

┌─────────────────────────────────────────────────────────────────┐
│                    E-COMMERCE EXAMPLE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PostgreSQL                 MongoDB                 Redis        │
│  ───────────                ─────────               ─────        │
│  • Users                    • Product catalog       • Sessions   │
│  • Orders                   • Reviews               • Cart       │
│  • Payments                 • Recommendations       • Rate limits│
│  • Inventory                                                     │
│                                                                  │
│  Elasticsearch              Cassandra                            │
│  ─────────────              ─────────                            │
│  • Product search           • Analytics events                   │
│  • Logs                     • User activity                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Indexing Decision Framework

```
When to create an index:
  ✓ Column frequently in WHERE clause
  ✓ Column used in JOIN conditions
  ✓ Column used in ORDER BY
  ✓ Column used in GROUP BY

When NOT to index:
  ✗ Small tables (< 1000 rows)
  ✗ Columns rarely queried
  ✗ Columns with low cardinality (e.g., boolean)
  ✗ Frequently updated columns (index overhead)

Index type selection:
  B-Tree (default): Range queries, equality, sorting
  Hash: Equality only, very fast
  GIN: Full-text search, arrays, JSONB
  GiST: Geometric data, full-text
```

---

## Sharding Decision Framework

```
When to shard:
  ✓ Single node can't handle data volume
  ✓ Single node can't handle write throughput
  ✓ Query performance degraded despite optimization

Shard key selection:
  Good:
    • user_id (even distribution, query locality)
    • tenant_id (multi-tenant apps)
    • hash(id) (even distribution)

  Bad:
    • created_at (hot spots on recent data)
    • country (uneven distribution)
    • auto-increment id (all writes to one shard)

Shard key checklist:
  □ High cardinality (many unique values)
  □ Even distribution
  □ Commonly used in queries
  □ Immutable (doesn't change)
```

---

## Replication Decision Framework

```
Single-Leader (Master-Slave):
  Use when:
    • Strong consistency needed
    • Clear read/write separation
    • Simpler operation

  Trade-off:
    • Write bottleneck
    • Failover complexity

Multi-Leader:
  Use when:
    • Geo-distributed writes
    • High write availability

  Trade-off:
    • Conflict resolution needed
    • Complexity

Leaderless (Quorum):
  Use when:
    • High availability priority
    • Tunable consistency needed

  Trade-off:
    • Read repair overhead
    • Quorum coordination
```

---

## Decision Checklist

```
Before finalizing database choice:

□ Identified primary access patterns
□ Estimated data volume (now and 5 years)
□ Determined read/write ratio
□ Defined consistency requirements
□ Considered scaling path
□ Evaluated operational complexity
□ Checked team expertise
□ Considered cost
□ Planned for backup/recovery
□ Documented trade-offs
```

---

## Next Steps

1. → [Caching Decisions](caching-decisions.md) - When and how to cache
2. → [Consistency Decisions](consistency-decisions.md) - CAP trade-offs
3. → [Scaling Decisions](scaling-decisions.md) - Scaling strategies
