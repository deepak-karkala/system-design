# Database Selection Guide

Choosing the right database is one of the most critical decisions in system design. This guide covers when to use different database types and how to make informed choices.

---

## Database Categories Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DATABASE LANDSCAPE                               │
├───────────────┬──────────────────┬───────────────────┬─────────────────┤
│ Relational    │ Document         │ Key-Value         │ Wide Column     │
│ (SQL)         │ (NoSQL)          │ (NoSQL)           │ (NoSQL)         │
├───────────────┼──────────────────┼───────────────────┼─────────────────┤
│ PostgreSQL    │ MongoDB          │ Redis             │ Cassandra       │
│ MySQL         │ CouchDB          │ DynamoDB          │ HBase           │
│ Oracle        │ Firestore        │ Memcached         │ ScyllaDB        │
│ SQL Server    │ DocumentDB       │ etcd              │ Bigtable        │
├───────────────┴──────────────────┴───────────────────┴─────────────────┤
│ Graph                │ Time-Series          │ Search              │
├──────────────────────┼──────────────────────┼─────────────────────┤
│ Neo4j                │ InfluxDB             │ Elasticsearch       │
│ Amazon Neptune       │ TimescaleDB          │ OpenSearch          │
│ JanusGraph           │ Prometheus           │ Algolia             │
│ Dgraph               │ QuestDB              │ Meilisearch         │
└──────────────────────┴──────────────────────┴─────────────────────┘
```

---

## Relational Databases (SQL)

### When to Use

```
✓ ACID transactions are required
✓ Complex queries with JOINs
✓ Data has clear relationships
✓ Schema is well-defined and stable
✓ Strong consistency is required
✓ Reporting and analytics needs
```

### When NOT to Use

```
✗ Massive write throughput (>50K writes/sec)
✗ Unstructured or highly variable schema
✗ Simple key-value access patterns
✗ Horizontal scaling is primary concern
✗ Schema evolves very frequently
```

### Comparison: PostgreSQL vs MySQL

```
Feature              │ PostgreSQL          │ MySQL
─────────────────────┼─────────────────────┼─────────────────────
JSON Support         │ Excellent (JSONB)   │ Good
Full-Text Search     │ Built-in            │ Limited
Extensions           │ Rich ecosystem      │ Fewer
Concurrency          │ MVCC (better)       │ MVCC
Replication          │ Streaming           │ Binary log
License              │ PostgreSQL (permissive)│ GPL
Use Case             │ Complex apps        │ Web apps, WordPress
```

### Scaling SQL Databases

```
Vertical Scaling:
  - Add more CPU, RAM, storage
  - Simple but has limits
  - Can handle 10K-50K QPS

Read Replicas:
  - Primary handles writes
  - Replicas handle reads
  - Replication lag consideration

Sharding:
  - Split data across servers
  - By user_id, tenant_id, etc.
  - Complex to implement and maintain

Connection Pooling:
  - PgBouncer, ProxySQL
  - Reduces connection overhead
  - Essential for high concurrency
```

---

## Document Databases

### When to Use

```
✓ Semi-structured data
✓ Flexible, evolving schema
✓ Hierarchical data (nested objects)
✓ Aggregating related data in one document
✓ Development speed priority
✓ Catalog, content management systems
```

### When NOT to Use

```
✗ Complex transactions across documents
✗ Many-to-many relationships
✗ Complex reporting with JOINs
✗ Strong consistency is critical
```

### MongoDB Design Principles

```
Embedding vs Referencing:

Embed when:
  - Data is accessed together
  - One-to-few relationship
  - Child doesn't exist without parent

  Example (Embedded):
  {
    "user_id": "123",
    "name": "John",
    "addresses": [
      {"type": "home", "city": "NYC"},
      {"type": "work", "city": "LA"}
    ]
  }

Reference when:
  - Large nested documents
  - Many-to-many relationships
  - Child accessed independently

  Example (Referenced):
  // users collection
  {"user_id": "123", "name": "John"}

  // orders collection
  {"order_id": "456", "user_id": "123", "amount": 100}
```

### MongoDB Scaling

```
Replica Sets:
  - 3+ nodes (1 primary, 2+ secondary)
  - Automatic failover
  - Read from secondaries (eventual consistency)

Sharding:
  - Automatic data distribution
  - Shard key selection is critical
  - Good: user_id (even distribution)
  - Bad: created_at (hot spots)
```

---

## Key-Value Stores

### When to Use

```
✓ Simple get/set operations
✓ High-speed lookups by key
✓ Caching layer
✓ Session storage
✓ Rate limiting counters
✓ Leaderboards
```

### When NOT to Use

```
✗ Complex queries needed
✗ Relationships between data
✗ Range queries
✗ Data larger than memory (depends on store)
```

### Redis Overview

```
Data Structures:
  - Strings: Simple values, counters
  - Lists: Queues, recent items
  - Sets: Unique collections, tags
  - Sorted Sets: Leaderboards, rankings
  - Hashes: Object-like storage
  - Streams: Event streaming

Use Cases:
  - Caching (TTL-based expiry)
  - Session storage
  - Rate limiting
  - Pub/Sub messaging
  - Real-time leaderboards
  - Distributed locks
```

### DynamoDB Overview

```
Key Concepts:
  - Partition Key: Required, determines partition
  - Sort Key: Optional, enables range queries
  - GSI: Global Secondary Index
  - LSI: Local Secondary Index

Capacity Modes:
  - Provisioned: Set RCU/WCU, predictable cost
  - On-demand: Pay per request, auto-scaling

Use Cases:
  - Serverless applications
  - Gaming (player data, sessions)
  - IoT (device data)
  - Mobile backends
```

---

## Wide Column Stores

### When to Use

```
✓ Massive write throughput
✓ Time-series data
✓ Event logging
✓ Large-scale data (petabytes)
✓ Write-heavy workloads
✓ Eventual consistency acceptable
```

### When NOT to Use

```
✗ Complex queries or JOINs
✗ Strong consistency required
✗ Frequent schema changes
✗ Small datasets
```

### Cassandra Overview

```
Architecture:
  - Masterless (all nodes equal)
  - Linear scalability
  - Tunable consistency
  - Partition-based distribution

Data Model:
  - Keyspace → Tables → Rows → Columns
  - Partition Key determines node
  - Clustering Key determines order within partition

Query Patterns:
  - Design table per query pattern
  - Denormalization is expected
  - No JOINs, limited aggregations
```

### Cassandra Design Example

```
Use Case: User activity log

CREATE TABLE user_activities (
    user_id UUID,
    activity_time TIMESTAMP,
    activity_type TEXT,
    details TEXT,
    PRIMARY KEY ((user_id), activity_time)
) WITH CLUSTERING ORDER BY (activity_time DESC);

Query: Get recent activities for user
SELECT * FROM user_activities
WHERE user_id = ? LIMIT 100;
```

---

## Graph Databases

### When to Use

```
✓ Highly connected data
✓ Relationship queries (friends of friends)
✓ Social networks
✓ Recommendation engines
✓ Fraud detection (connection patterns)
✓ Knowledge graphs
```

### When NOT to Use

```
✗ Simple CRUD operations
✗ Analytical queries on all data
✗ Write-heavy workloads
✗ Data with few relationships
```

### Neo4j Basics

```
Concepts:
  - Nodes: Entities (Person, Product)
  - Relationships: Connections (KNOWS, BOUGHT)
  - Properties: Attributes on nodes/relationships

Cypher Query Examples:

# Find friends of friends
MATCH (me:Person {name: 'John'})-[:KNOWS*2]-(fof:Person)
RETURN fof.name

# Product recommendations
MATCH (u:User)-[:PURCHASED]->(p:Product)<-[:PURCHASED]-(other:User)
      -[:PURCHASED]->(rec:Product)
WHERE u.id = '123' AND NOT (u)-[:PURCHASED]->(rec)
RETURN rec, count(*) as score
ORDER BY score DESC LIMIT 10
```

---

## Time-Series Databases

### When to Use

```
✓ Metrics and monitoring
✓ IoT sensor data
✓ Financial market data
✓ Log data with timestamps
✓ Analytics over time periods
```

### When NOT to Use

```
✗ General-purpose CRUD
✗ Complex relationships
✗ Frequent updates to historical data
```

### Time-Series Design Patterns

```
InfluxDB Concepts:
  - Measurement: Table equivalent
  - Tags: Indexed metadata
  - Fields: Actual values
  - Timestamp: Time of data point

Example:
  temperature,location=room1,sensor=A value=23.5 1609459200

TimescaleDB:
  - PostgreSQL extension
  - Hypertables for time-series
  - SQL compatibility
  - Compression and retention policies
```

---

## Search Engines

### When to Use

```
✓ Full-text search
✓ Fuzzy matching
✓ Faceted search
✓ Auto-complete
✓ Log analytics
✓ Complex aggregations
```

### Elasticsearch Overview

```
Concepts:
  - Index: Collection of documents
  - Document: JSON record
  - Mapping: Schema definition
  - Shards: Horizontal scaling
  - Replicas: High availability

Use Cases:
  - Product search
  - Log analysis (ELK Stack)
  - Application monitoring
  - Analytics dashboards

Not a Primary Database:
  - Use as secondary index
  - Sync from primary data store
  - Accept eventual consistency
```

---

## Database Selection Decision Tree

```
START
  │
  ├─ Need ACID transactions?
  │   ├─ Yes → SQL (PostgreSQL, MySQL)
  │   └─ No ↓
  │
  ├─ Simple key-value access?
  │   ├─ Yes → Need persistence?
  │   │         ├─ No → Redis (in-memory)
  │   │         └─ Yes → DynamoDB, Redis + AOF
  │   └─ No ↓
  │
  ├─ Write-heavy (>50K writes/sec)?
  │   ├─ Yes → Cassandra, ScyllaDB
  │   └─ No ↓
  │
  ├─ Time-series data?
  │   ├─ Yes → InfluxDB, TimescaleDB
  │   └─ No ↓
  │
  ├─ Full-text search needed?
  │   ├─ Yes → Elasticsearch (as secondary)
  │   └─ No ↓
  │
  ├─ Graph relationships?
  │   ├─ Yes → Neo4j, Neptune
  │   └─ No ↓
  │
  ├─ Flexible schema?
  │   ├─ Yes → MongoDB, DocumentDB
  │   └─ No → SQL (PostgreSQL, MySQL)
```

---

## Decision Matrix

```
Requirement              │ SQL  │ Mongo │ Redis │ Cassandra │ Neo4j
─────────────────────────┼──────┼───────┼───────┼───────────┼───────
ACID Transactions        │ ★★★  │ ★★    │ ★     │ ★         │ ★★
Complex Queries          │ ★★★  │ ★★    │ ★     │ ★         │ ★★★
Write Throughput         │ ★★   │ ★★    │ ★★★   │ ★★★       │ ★★
Read Latency             │ ★★   │ ★★    │ ★★★   │ ★★        │ ★★
Horizontal Scale         │ ★    │ ★★★   │ ★★    │ ★★★       │ ★
Schema Flexibility       │ ★    │ ★★★   │ ★★    │ ★★        │ ★★
Relationships            │ ★★★  │ ★     │ ★     │ ★         │ ★★★
Operational Simplicity   │ ★★★  │ ★★    │ ★★★   │ ★         │ ★★
```

---

## Multi-Database Architecture

Real systems often use multiple databases:

```
Example: E-commerce Platform

┌─────────────────────────────────────────────────────────────────┐
│                         Application                             │
├──────────────────┬──────────────────┬──────────────────────────┤
│                  │                  │                          │
│   PostgreSQL     │    MongoDB       │      Redis               │
│   ───────────    │    ────────      │      ─────               │
│   - Users        │    - Product     │   - Sessions             │
│   - Orders       │      catalog     │   - Cart cache           │
│   - Payments     │    - Reviews     │   - Rate limiting        │
│   - Transactions │                  │                          │
│                  │                  │                          │
├──────────────────┴──────────────────┴──────────────────────────┤
│                                                                 │
│                    Elasticsearch                                │
│                    ─────────────                                │
│                    - Product search                             │
│                    - Log analytics                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interview Questions to Consider

```
1. What's the read/write ratio?
2. How much data will be stored?
3. What are the access patterns?
4. Is ACID transaction support needed?
5. What's the consistency requirement?
6. How will the data grow over time?
7. What's the latency requirement?
8. Is horizontal scaling needed?
9. What queries will be run?
10. What's the budget/operational capacity?
```

---

## Next Steps

1. → [Schema Design](schema-design.md) - Design your data model
2. → [Consistency Patterns](consistency-patterns.md) - Understand CAP and PACELC
3. → [Deep Dive: Caching](../06-deep-dive/caching-strategies.md) - Layer caching on top
