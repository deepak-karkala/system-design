# Schema Design & Data Modeling

How to design effective database schemas with proper indexing, partitioning, and replication strategies.

---

## Schema Design Principles

### 1. Start with Access Patterns

```
Design your schema based on how data will be accessed, not how it's organized.

Questions to Ask:
- What are the most common queries?
- What's the read/write ratio?
- What data is accessed together?
- What are the latency requirements?
```

### 2. Denormalization Trade-offs

```
Normalized (3NF):
  Pros: No data duplication, easier updates
  Cons: Requires JOINs, slower reads

Denormalized:
  Pros: Fast reads, fewer JOINs
  Cons: Data duplication, complex updates

Rule of Thumb:
  - Read-heavy → Denormalize
  - Write-heavy → Normalize
  - Mixed → Strategic denormalization
```

---

## Indexing

### Index Types

```
Type              │ Description                    │ Use Case
──────────────────┼────────────────────────────────┼─────────────────────
B-Tree            │ Balanced tree, sorted          │ Range queries, equality
Hash              │ Hash table lookup              │ Equality only
Full-Text         │ Text search                    │ Search functionality
Spatial           │ Geometric data                 │ Geo queries
Composite         │ Multiple columns               │ Multi-column queries
Covering          │ Includes all query columns     │ Avoid table lookups
```

### B-Tree Index

```
Most common index type. Good for:
  - Equality: WHERE id = 123
  - Range: WHERE date > '2024-01-01'
  - Sorting: ORDER BY created_at
  - Prefix: WHERE name LIKE 'John%'

Not good for:
  - Suffix: WHERE name LIKE '%son'
  - Functions: WHERE YEAR(date) = 2024

Structure:
        [50]
       /    \
    [25]    [75]
    /  \    /  \
 [10] [30][60] [90]
```

### Composite Index

```
Index on multiple columns: (a, b, c)

Can be used for:
  - WHERE a = 1
  - WHERE a = 1 AND b = 2
  - WHERE a = 1 AND b = 2 AND c = 3
  - ORDER BY a, b

Cannot be used for:
  - WHERE b = 2 (missing leftmost column)
  - WHERE a = 1 AND c = 3 (missing middle column)

Order matters! Design for most selective first.
```

### Indexing Best Practices

```
DO:
  ✓ Index columns used in WHERE, JOIN, ORDER BY
  ✓ Put most selective columns first in composite indexes
  ✓ Use covering indexes for hot queries
  ✓ Monitor index usage with EXPLAIN
  ✓ Consider partial indexes for filtered queries

DON'T:
  ✗ Index every column
  ✗ Create duplicate indexes
  ✗ Index low-cardinality columns alone
  ✗ Ignore write performance impact
  ✗ Forget to maintain (REINDEX)
```

### Index Cost Analysis

```
Trade-offs:
  - Each index: +10-30% storage
  - Each index: +1-5ms write latency
  - Index scan vs table scan threshold: ~5-10% of rows

When to NOT index:
  - Very small tables (<1000 rows)
  - Columns rarely queried
  - Frequently updated columns
  - Very low cardinality (e.g., boolean)
```

---

## Partitioning

### Partitioning Strategies

```
Strategy          │ Description                    │ Use Case
──────────────────┼────────────────────────────────┼─────────────────────
Range             │ By value range                 │ Time-series, dates
List              │ By specific values             │ Regions, categories
Hash              │ By hash function               │ Even distribution
Composite         │ Combination                    │ Complex requirements
```

### Range Partitioning

```sql
-- Partition by date range
CREATE TABLE orders (
    id BIGINT,
    order_date DATE,
    customer_id INT,
    amount DECIMAL
) PARTITION BY RANGE (order_date);

CREATE TABLE orders_2024_q1 PARTITION OF orders
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

CREATE TABLE orders_2024_q2 PARTITION OF orders
    FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');

Benefits:
  - Queries on date ranges scan only relevant partitions
  - Easy to drop old data (drop partition)
  - Parallel query execution
```

### Hash Partitioning

```sql
-- Partition by hash of customer_id
CREATE TABLE orders (
    id BIGINT,
    customer_id INT,
    amount DECIMAL
) PARTITION BY HASH (customer_id);

CREATE TABLE orders_0 PARTITION OF orders
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE orders_1 PARTITION OF orders
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);
-- ... etc

Benefits:
  - Even data distribution
  - No hot spots
  - Scales write throughput
```

### Sharding (Horizontal Partitioning)

```
Distribute data across multiple database servers.

Shard Key Selection:
  Good:
    - user_id (even distribution, locality)
    - tenant_id (multi-tenant apps)
    - hash(id) (even distribution)

  Bad:
    - created_at (hot spots on recent shard)
    - country (uneven distribution)

Architecture:
  ┌─────────────┐
  │   Router    │
  └──────┬──────┘
         │
  ┌──────┴──────┐
  │             │
  ▼             ▼
┌─────┐      ┌─────┐
│Shard│      │Shard│
│  1  │      │  2  │
└─────┘      └─────┘

Challenges:
  - Cross-shard queries
  - Transactions across shards
  - Resharding (adding/removing shards)
  - Maintaining referential integrity
```

### Consistent Hashing

```
Distribute data with minimal reorganization when nodes change.

Hash Ring:
      0 (360°)
        *
    *       *  ← Node A
  *           *
 *             *
*       +       * ← Node B
 *             *
  *           *
    *       *
        *  ← Node C

Key lookup:
  1. Hash key to position on ring
  2. Walk clockwise to find first node
  3. That node owns the key

Virtual nodes:
  - Each physical node has multiple positions
  - Improves distribution
  - Smoother rebalancing
```

---

## Replication

### Replication Topologies

```
1. Single-Leader (Master-Slave):
   ┌────────┐
   │ Leader │ ←── Writes
   └───┬────┘
       │ Replication
   ┌───┴────┬────────┐
   │        │        │
   ▼        ▼        ▼
┌──────┐ ┌──────┐ ┌──────┐
│Follower│Follower│Follower│ ←── Reads
└──────┘ └──────┘ └──────┘

Pros: Strong consistency, simple
Cons: Write bottleneck, failover complexity

2. Multi-Leader:
   ┌────────┐     ┌────────┐
   │Leader 1│ ←─→ │Leader 2│
   └───┬────┘     └───┬────┘
       │              │
   ┌───┴───┐      ┌───┴───┐
   │Follower│     │Follower│
   └───────┘      └───────┘

Pros: Geo-distributed writes
Cons: Conflict resolution needed

3. Leaderless (Dynamo-style):
   ┌──────┐   ┌──────┐   ┌──────┐
   │Node 1│ ← │Client│ → │Node 2│
   └──────┘   └──────┘   └──────┘
       ↑                     ↑
       └──────────┬──────────┘
              ┌───┴───┐
              │Node 3 │
              └───────┘

Quorum: W + R > N for consistency
```

### Replication Lag

```
Sync vs Async Replication:

Synchronous:
  - Write confirmed only after replicas acknowledge
  - Guarantees no data loss
  - Higher latency (wait for slowest replica)

Asynchronous:
  - Write confirmed after leader writes
  - Lower latency
  - Potential data loss on leader failure
  - Replication lag possible

Semi-synchronous:
  - Wait for at least one replica
  - Balance between safety and performance
```

### Read Consistency Levels

```
Level              │ Guarantee                      │ Use Case
───────────────────┼────────────────────────────────┼─────────────────
Read-your-writes   │ See own writes immediately     │ User profiles
Monotonic reads    │ Never see older data           │ Dashboards
Bounded staleness  │ Max lag time guaranteed        │ Analytics
Strong consistency │ All reads see latest write     │ Transactions
```

---

## Schema Design Patterns

### Pattern 1: Soft Deletes

```sql
-- Instead of deleting, mark as deleted
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP NULL;

-- Queries exclude deleted
SELECT * FROM users WHERE deleted_at IS NULL;

-- Partial index for performance
CREATE INDEX idx_active_users ON users (email)
    WHERE deleted_at IS NULL;

Benefits:
  - Easy recovery
  - Audit trail
  - Referential integrity preserved
```

### Pattern 2: Audit Logging

```sql
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100),
    record_id BIGINT,
    action VARCHAR(20), -- INSERT, UPDATE, DELETE
    old_data JSONB,
    new_data JSONB,
    changed_by BIGINT,
    changed_at TIMESTAMP DEFAULT NOW()
);

-- Trigger-based or application-level logging
```

### Pattern 3: Event Sourcing

```sql
-- Store events, not current state
CREATE TABLE account_events (
    id BIGSERIAL PRIMARY KEY,
    account_id UUID,
    event_type VARCHAR(50),
    event_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Events:
INSERT INTO account_events (account_id, event_type, event_data) VALUES
    ('uuid', 'ACCOUNT_OPENED', '{"initial_balance": 1000}'),
    ('uuid', 'DEPOSIT', '{"amount": 500}'),
    ('uuid', 'WITHDRAWAL', '{"amount": 200}');

-- Current state = replay all events
-- Materialized view for current balances
```

### Pattern 4: Polymorphic Associations

```sql
-- Option 1: Single Table Inheritance
CREATE TABLE notifications (
    id BIGSERIAL PRIMARY KEY,
    type VARCHAR(50), -- 'email', 'sms', 'push'
    recipient VARCHAR(255),
    -- Email specific
    subject VARCHAR(255),
    body TEXT,
    -- SMS specific
    phone_number VARCHAR(20),
    -- Push specific
    device_token VARCHAR(255)
);

-- Option 2: Concrete Table Inheritance
CREATE TABLE email_notifications (...);
CREATE TABLE sms_notifications (...);
CREATE TABLE push_notifications (...);

-- Option 3: JSONB for flexible attributes
CREATE TABLE notifications (
    id BIGSERIAL PRIMARY KEY,
    type VARCHAR(50),
    attributes JSONB
);
```

### Pattern 5: Hierarchical Data

```sql
-- Option 1: Adjacency List (simple but slow for deep queries)
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    parent_id INT REFERENCES categories(id)
);

-- Option 2: Materialized Path (fast reads)
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    path VARCHAR(255) -- e.g., '/1/5/12/'
);
-- Find all children: WHERE path LIKE '/1/5/%'

-- Option 3: Nested Sets (fast subtree queries)
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    lft INT,
    rgt INT
);
-- Find all children: WHERE lft > parent.lft AND rgt < parent.rgt
```

---

## Schema Evolution

### Backward Compatible Changes

```
Safe changes:
  ✓ Add nullable column
  ✓ Add table
  ✓ Add index (non-blocking in some DBs)
  ✓ Add default value
  ✓ Widen column (VARCHAR(50) → VARCHAR(100))

Unsafe changes (require migration strategy):
  ✗ Remove column
  ✗ Rename column
  ✗ Change column type
  ✗ Add NOT NULL constraint
```

### Migration Strategies

```
1. Expand-Contract Pattern:
   a. Add new column (nullable)
   b. Backfill data
   c. Update application to use both
   d. Stop using old column
   e. Remove old column

2. Dual-Write:
   a. Write to both old and new
   b. Backfill old data to new
   c. Switch reads to new
   d. Stop writes to old

3. Shadow Writes:
   a. Write to new in shadow
   b. Compare results
   c. Switch when confident
```

---

## Interview Checklist

```
□ Identify access patterns
□ Choose normalization level
□ Design primary keys
□ Plan indexes for hot queries
□ Consider partitioning strategy
□ Plan replication topology
□ Handle schema evolution
□ Document trade-offs made
```

---

## Next Steps

1. → [Consistency Patterns](consistency-patterns.md) - CAP, ACID, BASE
2. → [Caching Strategies](../06-deep-dive/caching-strategies.md) - Layer caching
3. → [High-Level Design](../05-high-level-design/) - System architecture
