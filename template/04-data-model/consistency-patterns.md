# Consistency Patterns

Understanding consistency models is crucial for designing distributed systems. This guide covers CAP theorem, ACID, BASE, and practical consistency patterns.

---

## CAP Theorem

### The Three Properties

```
╔════════════════════════════════════════════════════════════════╗
║                       CAP THEOREM                               ║
║   In a distributed system, you can only guarantee 2 of 3:      ║
╠════════════════════════════════════════════════════════════════╣
║                                                                 ║
║   ┌───────────────────┐                                        ║
║   │   Consistency     │  All nodes see same data at same time  ║
║   └─────────┬─────────┘                                        ║
║             │                                                   ║
║      ┌──────┴──────┐                                           ║
║      │             │                                            ║
║   ┌──▼───┐     ┌───▼──┐                                        ║
║   │  A   │     │  P   │                                        ║
║   └──────┘     └──────┘                                        ║
║                                                                 ║
║   Availability         Partition Tolerance                     ║
║   Every request        System works despite                    ║
║   gets a response      network failures                        ║
╚════════════════════════════════════════════════════════════════╝
```

### CAP Trade-offs

```
In practice, network partitions WILL happen.
So you must choose between C and A during partitions.

CP (Consistency + Partition Tolerance):
  - Returns error if can't guarantee consistency
  - Examples: MongoDB, HBase, Redis (in cluster mode)
  - Use when: Financial transactions, inventory

AP (Availability + Partition Tolerance):
  - Returns potentially stale data
  - Examples: Cassandra, DynamoDB, CouchDB
  - Use when: Social media, analytics, caching

CA (Consistency + Availability):
  - Not possible in distributed systems
  - Only works in single-node systems
  - Examples: Traditional RDBMS (single node)
```

### CAP in Real Systems

```
System          │ Default │ Configurable │ Notes
────────────────┼─────────┼──────────────┼────────────────────
PostgreSQL      │ CP      │ No           │ Single leader, ACID
MySQL           │ CP      │ No           │ Single leader, ACID
MongoDB         │ CP      │ Yes          │ Can tune for AP
Cassandra       │ AP      │ Yes          │ Tunable consistency
DynamoDB        │ AP      │ Yes          │ Strong consistency option
Redis Cluster   │ AP      │ No           │ Async replication
CockroachDB     │ CP      │ No           │ Serializable by default
```

---

## ACID vs BASE

### ACID (Traditional Databases)

```
Atomicity:
  - Transaction is all-or-nothing
  - If any part fails, entire transaction rolls back

  Example:
    BEGIN;
    UPDATE accounts SET balance = balance - 100 WHERE id = 1;
    UPDATE accounts SET balance = balance + 100 WHERE id = 2;
    COMMIT;  -- Both succeed or both fail

Consistency:
  - Database moves from one valid state to another
  - Constraints are enforced

Isolation:
  - Concurrent transactions don't interfere
  - Isolation levels: READ UNCOMMITTED → SERIALIZABLE

Durability:
  - Committed transactions survive crashes
  - Written to persistent storage
```

### ACID Isolation Levels

```
Level               │ Dirty Read │ Non-Repeatable │ Phantom
────────────────────┼────────────┼────────────────┼──────────
READ UNCOMMITTED    │ Possible   │ Possible       │ Possible
READ COMMITTED      │ Prevented  │ Possible       │ Possible
REPEATABLE READ     │ Prevented  │ Prevented      │ Possible
SERIALIZABLE        │ Prevented  │ Prevented      │ Prevented

Dirty Read: See uncommitted changes from other transactions
Non-Repeatable Read: Same query returns different results
Phantom Read: New rows appear matching a range query
```

### BASE (NoSQL Approach)

```
Basically Available:
  - System is available most of the time
  - May return stale or incomplete data

Soft State:
  - State may change over time
  - Even without input (due to eventual consistency)

Eventually Consistent:
  - Given enough time, all replicas converge
  - No guarantee on how long

BASE Trade-offs:
  + Higher availability
  + Better scalability
  + Lower latency
  - No guaranteed consistency
  - Application must handle inconsistency
  - Complex error handling
```

### ACID vs BASE Comparison

```
Aspect           │ ACID                │ BASE
─────────────────┼─────────────────────┼─────────────────────
Consistency      │ Strong              │ Eventual
Availability     │ May block           │ Always available
Scalability      │ Vertical mainly     │ Horizontal
Transaction      │ Multi-statement     │ Single operation
Use Case         │ Financial, orders   │ Social, analytics
Databases        │ PostgreSQL, MySQL   │ Cassandra, DynamoDB
```

---

## PACELC Theorem

### Extension of CAP

```
PACELC: If there's a Partition (P), choose Availability (A) or Consistency (C);
        Else (E), choose Latency (L) or Consistency (C).

Why it matters:
  - CAP only addresses partition scenarios
  - PACELC addresses normal operation too
  - In normal operation: trade-off is latency vs consistency

System Examples:
  - PA/EL: DynamoDB, Cassandra (default) - Prefer availability and latency
  - PC/EC: MongoDB, HBase - Prefer consistency always
  - PA/EC: Rare - Available during partition, consistent normally
  - PC/EL: PNUTS - Consistent during partition, low latency normally
```

### PACELC Decision Matrix

```
During Partition (P):                 Normal Operation (E):
┌─────────────────────────┐          ┌─────────────────────────┐
│ Choose Availability (A) │    OR    │ Choose Latency (L)      │
│ - Always respond        │          │ - Fast async replication│
│ - May be stale         │          │ - May have stale reads  │
├─────────────────────────┤          ├─────────────────────────┤
│ Choose Consistency (C)  │    OR    │ Choose Consistency (C)  │
│ - May not respond       │          │ - Sync replication      │
│ - Data is correct       │          │ - Higher latency        │
└─────────────────────────┘          └─────────────────────────┘
```

---

## Consistency Patterns

### 1. Strong Consistency

```
Every read returns the most recent write.

Implementation:
  - Synchronous replication
  - Consensus protocols (Raft, Paxos)
  - Single leader with blocking reads

Example (Raft Consensus):
  1. Client sends write to leader
  2. Leader replicates to majority (quorum)
  3. Leader commits after majority ack
  4. Leader responds to client
  5. All reads go to leader

Latency: Higher (wait for quorum)
Use when: Financial transactions, inventory
```

### 2. Eventual Consistency

```
All replicas eventually converge to same value.

Implementation:
  - Asynchronous replication
  - Anti-entropy protocols
  - Conflict resolution strategies

Conflict Resolution:
  - Last-Write-Wins (LWW): Timestamp-based
  - Version Vectors: Track causality
  - CRDTs: Conflict-free data structures

Latency: Lower (async)
Use when: Social feeds, like counts, DNS
```

### 3. Read-Your-Writes

```
User always sees their own writes immediately.

Implementation Options:

Option 1: Sticky sessions
  - Route user to same replica
  - Read from that replica

Option 2: Write-then-read from leader
  - After write, read from leader temporarily
  - Fall back to replica after delay

Option 3: Version tracking
  - Client tracks last write version
  - Read request includes version
  - Wait until replica has that version

Use when: User profile updates, settings
```

### 4. Monotonic Reads

```
Once a value is seen, never see an older value.

Problem:
  Read 1: Replica A → balance = 100
  Read 2: Replica B → balance = 80 (stale!)

Solution:
  - Session stickiness
  - Version tracking
  - Always read from same or newer version

Use when: Dashboards, progress tracking
```

### 5. Causal Consistency

```
If operation A caused operation B, everyone sees A before B.

Example:
  User 1: Posts "Hello"
  User 2: Replies "Hi" (caused by seeing "Hello")

Everyone should see:
  "Hello" before "Hi"
  Never "Hi" without "Hello"

Implementation:
  - Vector clocks
  - Lamport timestamps
  - Dependency tracking

Use when: Messaging, comments, social features
```

### 6. Quorum Consistency

```
W + R > N guarantees overlap between read and write nodes.

N = Total replicas
W = Write quorum (nodes that must ack write)
R = Read quorum (nodes that must respond to read)

Common configurations:
  Strong consistency: W=N, R=1 or W=1, R=N
  Balanced: W=ceil((N+1)/2), R=ceil((N+1)/2)
  Read-heavy: W=N, R=1
  Write-heavy: W=1, R=N

Example (N=3):
  W=2, R=2: Guaranteed consistency
  W=1, R=1: Fast but eventually consistent

  ┌──────┐  ┌──────┐  ┌──────┐
  │Node 1│  │Node 2│  │Node 3│
  └──────┘  └──────┘  └──────┘
      │         │         │
      └────┬────┴────┬────┘
           │         │
        Write(2)   Read(2)
           ↓         ↓
     At least 1 node in common!
```

---

## Consistency in Practice

### Decision Framework

```
Question                           │ If Yes               │ If No
───────────────────────────────────┼──────────────────────┼───────────────
Can users see stale data?          │ Eventual consistency │ Strong consistency
Is data financial/inventory?       │ Strong consistency   │ Consider eventual
Is low latency critical?           │ Eventual consistency │ Strong okay
Are there concurrent writers?      │ Need conflict resolution │ Simpler model
Is global distribution needed?     │ Eventual preferred   │ Strong viable
```

### Hybrid Approaches

```
Real systems often use different consistency for different data:

Example: E-commerce Platform

┌─────────────────────────────────────────────────────────────────┐
│                     Data Consistency Map                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Strong Consistency (CP):                                       │
│  ├── Inventory counts                                           │
│  ├── Payment transactions                                       │
│  ├── Order status                                               │
│  └── User authentication                                        │
│                                                                 │
│  Eventual Consistency (AP):                                     │
│  ├── Product reviews                                            │
│  ├── View counts                                                │
│  ├── Recommendations                                            │
│  └── Search results                                             │
│                                                                 │
│  Read-Your-Writes:                                              │
│  ├── Shopping cart                                              │
│  └── User profile                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Handling Inconsistency

```
Application Strategies:

1. Optimistic UI:
   - Show expected result immediately
   - Reconcile when server confirms
   - Rollback if conflict

2. Conflict Resolution:
   - Merge changes (CRDTs)
   - Last-write-wins
   - User resolution

3. Compensation:
   - Saga pattern
   - Eventual correction
   - Notification on conflict

4. Idempotency:
   - Handle duplicate operations
   - Idempotency keys
   - Deduplication
```

---

## Interview Tips

### Questions to Ask

```
1. What happens if users see stale data?
   → Determines if eventual consistency is acceptable

2. What's the read/write ratio?
   → Affects quorum configuration

3. Are there concurrent updates to same data?
   → Need conflict resolution strategy

4. What's the acceptable latency?
   → Affects consistency choice

5. Is the system globally distributed?
   → Impacts replication strategy
```

### Common Mistakes

```
✗ Assuming strong consistency everywhere
✗ Not considering network partitions
✗ Ignoring replication lag
✗ Mixing consistency requirements
✗ Not documenting consistency guarantees
```

### Key Points to Demonstrate

```
✓ Understand CAP trade-offs
✓ Know when to use each consistency model
✓ Can design for specific use cases
✓ Understand implementation implications
✓ Consider hybrid approaches
```

---

## Summary Table

```
Model              │ Guarantee                 │ Trade-off          │ Example
───────────────────┼───────────────────────────┼────────────────────┼────────────
Strong             │ Latest value always       │ Higher latency     │ Banking
Eventual           │ Converges eventually      │ Stale reads        │ Social
Read-your-writes   │ See own writes            │ Session stickiness │ Profile
Monotonic          │ Never see older           │ Ordering overhead  │ Dashboard
Causal             │ Causality preserved       │ Dependency tracking│ Chat
Quorum             │ Configurable (W+R>N)      │ Latency vs accuracy│ DynamoDB
```

---

## Next Steps

1. → [Deep Dive: Caching](../06-deep-dive/caching-strategies.md) - Cache consistency
2. → [Deep Dive: Message Queues](../06-deep-dive/message-queues.md) - Delivery guarantees
3. → [Case Studies](../10-case-studies/) - See patterns in practice
