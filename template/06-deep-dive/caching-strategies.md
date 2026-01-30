# Caching Strategies Deep Dive

A comprehensive guide to caching patterns, strategies, and implementation considerations.

---

## Why Cache?

```
Benefits:
  - Reduce latency (ms → μs)
  - Reduce database load
  - Improve throughput
  - Handle traffic spikes
  - Save costs (fewer DB queries)

Cost:
  - Additional infrastructure
  - Complexity (invalidation)
  - Memory costs
  - Consistency challenges
```

---

## Caching Patterns

### 1. Cache-Aside (Lazy Loading)

```
┌──────────┐     1. Check cache     ┌───────────┐
│          │ ─────────────────────> │           │
│  Client  │                        │   Cache   │
│          │ <───────────────────── │           │
└──────────┘     2. Cache miss      └───────────┘
      │
      │ 3. Query database
      ▼
┌───────────┐
│ Database  │
└───────────┘
      │
      │ 4. Return data
      ▼
┌──────────┐     5. Store in cache  ┌───────────┐
│  Client  │ ─────────────────────> │   Cache   │
└──────────┘                        └───────────┘

Pseudocode:
  def get(key):
      value = cache.get(key)
      if value is None:  # Cache miss
          value = database.get(key)
          cache.set(key, value, ttl=3600)
      return value

Pros:
  ✓ Only requested data is cached
  ✓ Cache failure doesn't break system
  ✓ Simple to implement

Cons:
  ✗ Cache miss = higher latency (DB + cache write)
  ✗ Data can become stale
  ✗ Initial requests always hit database
```

### 2. Write-Through

```
┌──────────┐     1. Write request   ┌───────────┐
│          │ ─────────────────────> │           │
│  Client  │                        │   Cache   │
│          │                        │           │
└──────────┘                        └─────┬─────┘
                                          │
                                    2. Write to DB
                                          │
                                          ▼
                                    ┌───────────┐
                                    │ Database  │
                                    └───────────┘
                                          │
                                    3. Confirm
                                          │
┌──────────┐     4. Response        ┌─────▼─────┐
│  Client  │ <───────────────────── │   Cache   │
└──────────┘                        └───────────┘

Pseudocode:
  def set(key, value):
      cache.set(key, value)
      database.set(key, value)  # Synchronous
      return success

Pros:
  ✓ Cache always consistent with DB
  ✓ Simple consistency model
  ✓ Read immediately after write works

Cons:
  ✗ Higher write latency (two writes)
  ✗ Cache fills with unread data
  ✗ Both must succeed
```

### 3. Write-Behind (Write-Back)

```
┌──────────┐     1. Write request   ┌───────────┐
│          │ ─────────────────────> │           │
│  Client  │                        │   Cache   │
│          │ <───────────────────── │           │
└──────────┘     2. Immediate ACK   └─────┬─────┘
                                          │
                                    3. Async write
                                    (batched/delayed)
                                          │
                                          ▼
                                    ┌───────────┐
                                    │ Database  │
                                    └───────────┘

Pseudocode:
  def set(key, value):
      cache.set(key, value)
      write_queue.add(key, value)  # Async
      return success  # Immediate return

  # Background worker
  def flush_to_database():
      while True:
          batch = write_queue.get_batch(100)
          database.bulk_write(batch)

Pros:
  ✓ Very fast writes
  ✓ Batching reduces DB load
  ✓ Absorbs write spikes

Cons:
  ✗ Risk of data loss if cache fails
  ✗ Complexity in failure handling
  ✗ Consistency window
```

### 4. Read-Through

```
┌──────────┐     1. Get request     ┌───────────┐
│          │ ─────────────────────> │           │
│  Client  │                        │   Cache   │
│          │                        │ (fetches  │
└──────────┘                        │  on miss) │
                                    └─────┬─────┘
                                          │
                                    2. If miss, fetch
                                          │
                                          ▼
                                    ┌───────────┐
                                    │ Database  │
                                    └───────────┘
                                          │
                                    3. Return & cache
                                          │
┌──────────┐     4. Response        ┌─────▼─────┐
│  Client  │ <───────────────────── │   Cache   │
└──────────┘                        └───────────┘

Difference from Cache-Aside:
  - Cache handles fetching, not application
  - Simpler application code
  - Cache library/service does the work

Pros:
  ✓ Simpler application logic
  ✓ Cache manages consistency

Cons:
  ✗ Requires cache library support
  ✗ Less control over behavior
```

### 5. Refresh-Ahead

```
Proactively refresh cache before expiry

TTL = 60 seconds
Refresh threshold = 50 seconds (at 83% of TTL)

Timeline:
  t=0s   : Cache populated
  t=50s  : Access triggers background refresh
  t=60s  : New data already in cache

Pseudocode:
  def get(key):
      value, remaining_ttl = cache.get_with_ttl(key)
      if remaining_ttl < REFRESH_THRESHOLD:
          async_refresh(key)  # Background
      return value

Pros:
  ✓ Reduces cache misses
  ✓ Fresh data for hot keys
  ✓ No user-facing latency for refresh

Cons:
  ✗ More complex implementation
  ✗ May refresh unused data
```

---

## Cache Invalidation

### Strategies

```
1. TTL-based (Time-To-Live):
   cache.set(key, value, ttl=3600)  # Expires in 1 hour

   Pros: Simple, automatic
   Cons: Data stale until expiry

2. Event-driven:
   def update_user(user_id, data):
       database.update(user_id, data)
       cache.delete(f"user:{user_id}")
       publish_event("user_updated", user_id)

   Pros: Immediate consistency
   Cons: Requires event infrastructure

3. Version-based:
   cache.set(f"user:{user_id}:v{version}", value)

   Pros: Immutable entries, simple
   Cons: Storage for old versions

4. Tag-based (Surrogate Keys):
   cache.set(key, value, tags=["user:123", "team:456"])
   cache.invalidate_by_tag("user:123")  # Invalidates all

   Pros: Group invalidation
   Cons: Requires cache support
```

### Invalidation Challenges

```
Problem: Cache Stampede (Thundering Herd)
  Many requests hit expired key simultaneously
  All request database
  Database overwhelmed

Solutions:
  1. Locking (only one fetches):
     if cache.miss(key):
         if cache.acquire_lock(key):
             value = database.get(key)
             cache.set(key, value)
             cache.release_lock(key)
         else:
             wait_or_retry()

  2. Stale-while-revalidate:
     Serve stale data while refreshing in background

  3. Probabilistic expiry:
     Add random jitter to TTL
     ttl = base_ttl + random(0, 60)
```

---

## Eviction Policies

```
Policy              │ Description                    │ Best For
────────────────────┼────────────────────────────────┼────────────────────
LRU (Least Recently │ Evict oldest accessed          │ General purpose
    Used)           │                                │
LFU (Least Freq.    │ Evict least accessed           │ Stable access patterns
    Used)           │                                │
FIFO (First In      │ Evict oldest inserted          │ Simple, predictable
    First Out)      │                                │
TTL (Time To Live)  │ Evict after time limit         │ Freshness important
Random              │ Random eviction                │ Simple, unpredictable
LRU-K               │ Based on K-th access           │ Scan resistance
ARC (Adaptive       │ Adapts between LRU/LFU         │ Unknown patterns
    Replacement)    │                                │

Redis default: LRU approximation (sampled LRU)
Memcached default: LRU
```

---

## Distributed Caching

### Single Node vs Cluster

```
Single Node:
  ┌─────────────┐
  │ App Server  │ ──────> Redis (single)
  └─────────────┘

  Limit: Memory of one machine (~100GB typical)
  Risk: Single point of failure

Cluster:
  ┌─────────────┐         ┌─────────┐
  │ App Server  │ ──────> │ Redis   │
  └─────────────┘         │ Cluster │
                          │ ┌─┬─┬─┐ │
                          │ │1│2│3│ │
                          │ └─┴─┴─┘ │
                          └─────────┘

  Scale: Unlimited (add nodes)
  HA: Replication + failover
```

### Consistent Hashing

```
Distribute keys across nodes with minimal redistribution

Hash Ring:
          Node A
            │
    ┌───────●───────┐
    │               │
Node D ●           ● Node B
    │               │
    └───────●───────┘
            │
          Node C

Key lookup:
  1. Hash key to position on ring
  2. Walk clockwise to first node
  3. That node owns the key

Adding/removing node:
  Only affects adjacent keys (minimal reshuffling)
```

---

## Redis Best Practices

### Data Structures

```
Structure    │ Use Case                      │ Commands
─────────────┼───────────────────────────────┼─────────────────
String       │ Simple key-value, counters    │ GET, SET, INCR
Hash         │ Object properties             │ HGET, HSET, HMGET
List         │ Queues, recent items          │ LPUSH, RPOP, LRANGE
Set          │ Unique items, tags            │ SADD, SMEMBERS, SINTER
Sorted Set   │ Leaderboards, rankings        │ ZADD, ZRANGE, ZRANK
Stream       │ Event logs, messaging         │ XADD, XREAD, XRANGE
```

### Memory Optimization

```
Key naming:
  ✓ user:123:profile     (structured)
  ✗ userProfileForUser123  (verbose)

Compression:
  - Compress large values before storing
  - MessagePack instead of JSON
  - gzip for large strings

TTL everything:
  - Set TTL on all keys
  - Prevents memory leaks
  - Default: 24 hours for cache

Monitor memory:
  INFO memory
  MEMORY USAGE key
  MEMORY DOCTOR
```

---

## Cache Sizing

### Estimation Formula

```
Cache Size = Hot Data Size × Overhead Factor

Hot Data Size:
  - 80/20 rule: 20% of data serves 80% of requests
  - Estimate: Active users × Data per user

Overhead Factor:
  - Redis: 1.5-2x for data structures
  - Serialization: 1.1-1.3x

Example (User Profiles):
  - DAU: 10 million
  - Profile size: 2 KB
  - Hot users (20%): 2 million

  Cache size = 2M × 2 KB × 1.5 = 6 GB
  With headroom (50%): 9 GB
```

### Hit Ratio Target

```
Hit Ratio = Cache Hits / (Cache Hits + Cache Misses)

Target: >90% for production caches

Improving hit ratio:
  - Increase cache size
  - Better key design
  - Longer TTL (if acceptable)
  - Warm cache on startup
  - Pre-fetch predictable data
```

---

## Caching Anti-Patterns

```
1. Cache Everything:
   ✗ Caching data accessed once
   ✓ Cache only hot data

2. No TTL:
   ✗ Data never expires
   ✓ Always set TTL, even if long

3. Cache Null:
   ✗ Cache miss for non-existent key loops
   ✓ Cache "not found" with short TTL

4. Single Large Value:
   ✗ One key with all user data
   ✓ Split into logical pieces

5. Cache in Code Path:
   ✗ Blocking on cache failure
   ✓ Graceful fallback to database
```

---

## Interview Tips

### Questions to Ask

```
1. What's the read/write ratio?
   → High reads = good cache candidate

2. How frequently does data change?
   → Frequent changes = short TTL or event-driven

3. Is stale data acceptable?
   → Affects TTL and invalidation strategy

4. What's the data access pattern?
   → Hot/cold determines sizing

5. What's the latency requirement?
   → Determines cache layer priority
```

### Key Points to Discuss

```
✓ Cache placement (where in architecture)
✓ Caching strategy (aside, through, behind)
✓ Invalidation approach
✓ Eviction policy
✓ Failure handling
✓ Cache warming strategy
✓ Monitoring and metrics
```

---

## Next Steps

1. → [Message Queues](message-queues.md) - Async processing
2. → [Load Balancing](load-balancing.md) - Traffic distribution
3. → [Case Studies](../10-case-studies/) - See caching in practice
