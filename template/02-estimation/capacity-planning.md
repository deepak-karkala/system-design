# Capacity Planning & Back-of-Envelope Estimation

Back-of-envelope calculations help you quickly estimate system requirements and identify potential bottlenecks before diving into design.

---

## Overview

**Purpose of Estimation:**
- Determine infrastructure requirements
- Identify system bottlenecks
- Make informed technology choices
- Validate design feasibility
- Communicate scale to interviewers

**Key Principle:** Estimates should be rough but reasonable. Round numbers for easy calculation.

---

## Quick Reference: Numbers Everyone Should Know

### Latency Numbers
```
Operation                           | Time
------------------------------------|-------------
L1 cache reference                  | 0.5 ns
L2 cache reference                  | 7 ns
Main memory reference               | 100 ns
SSD random read                     | 150 μs
HDD seek                            | 10 ms
Network round trip (same DC)        | 0.5 ms
Network round trip (cross-region)   | 150 ms
```

### Data Size References
```
Unit     | Size            | Example
---------|-----------------|------------------------
1 Byte   | 8 bits          | A single character
1 KB     | 1,000 bytes     | A short email
1 MB     | 1,000 KB        | A high-res photo
1 GB     | 1,000 MB        | A movie
1 TB     | 1,000 GB        | 500 hours of video
1 PB     | 1,000 TB        | 3 years of Earth photos
```

### Traffic References
```
Scale         | Requests/Day  | Requests/Second
--------------|---------------|----------------
1 Million     | 1,000,000     | ~12 RPS
10 Million    | 10,000,000    | ~116 RPS
100 Million   | 100,000,000   | ~1,160 RPS
1 Billion     | 1,000,000,000 | ~11,600 RPS
```

### Power of 2 References
```
Power  | Exact Value      | Approximate
-------|------------------|-------------
2^10   | 1,024            | ~1 Thousand (1 KB)
2^20   | 1,048,576        | ~1 Million (1 MB)
2^30   | 1,073,741,824    | ~1 Billion (1 GB)
2^40   | 1,099,511,627,776| ~1 Trillion (1 TB)
```

---

## The Four Pillars of Estimation

### 1. Traffic Estimation

**Formula:**
```
Daily Active Users (DAU) × Actions per User per Day = Daily Requests
Daily Requests ÷ 86,400 seconds = Average QPS
Average QPS × Peak Factor = Peak QPS
```

**Example: Twitter-like Service**
```
Given:
- DAU: 200 million
- Each user: 10 reads (timeline), 1 tweet per day
- Read:Write ratio: 10:1

Calculation:
Reads:  200M × 10 = 2 billion reads/day
Writes: 200M × 1 = 200 million writes/day

Average QPS:
- Reads:  2B ÷ 86,400 ≈ 23,000 read QPS
- Writes: 200M ÷ 86,400 ≈ 2,300 write QPS

Peak QPS (assuming 3x peak factor):
- Reads:  23,000 × 3 ≈ 70,000 read QPS
- Writes: 2,300 × 3 ≈ 7,000 write QPS
```

**Quick Conversions:**
```
1M requests/day ≈ 12 requests/second
1B requests/day ≈ 12,000 requests/second

Seconds in a day: 86,400 ≈ 100,000 (for easy math)
```

---

### 2. Storage Estimation

**Formula:**
```
Storage = Objects × Size per Object × Retention Period × Replication Factor
```

**Example: Photo Sharing Service**
```
Given:
- DAU: 100 million
- Photos per user per day: 2
- Average photo size: 500 KB
- Retention: 5 years
- Replication factor: 3

Daily new photos:
100M × 2 = 200 million photos/day

Daily storage:
200M × 500 KB = 100 TB/day

5-year storage:
100 TB × 365 × 5 = 182.5 PB

With replication:
182.5 PB × 3 = 547.5 PB
```

**Storage Types to Consider:**
```
Component          | Size Estimate
-------------------|-------------------
User profile       | 1-10 KB
Tweet/Post         | 0.5-1 KB
Image (original)   | 1-5 MB
Image (thumbnail)  | 10-50 KB
Video (1 min)      | 50-100 MB
Metadata           | 0.1-1 KB per object
Indexes            | 10-30% of data size
```

---

### 3. Bandwidth Estimation

**Formula:**
```
Bandwidth = Data Transfer per Day ÷ 86,400 seconds
```

**Example: Video Streaming Service**
```
Given:
- DAU: 50 million
- Videos watched per user: 3
- Average video length: 10 minutes
- Bitrate: 5 Mbps

Daily data transfer:
50M users × 3 videos × 10 min × 60 sec × 5 Mbps = 450 Petabits/day
= 56.25 PB/day

Average bandwidth:
56.25 PB ÷ 86,400 ≈ 650 TB/hour ≈ 5.2 Tbps

Peak bandwidth (3x):
5.2 Tbps × 3 ≈ 15.6 Tbps
```

**Bandwidth Considerations:**
```
Direction  | Description                | Typically
-----------|---------------------------|----------
Ingress    | Data coming into system    | Lower (uploads)
Egress     | Data going out of system   | Higher (downloads)

Note: Cloud providers often charge more for egress.
```

---

### 4. Memory/Cache Estimation

**Formula (80/20 Rule):**
```
Cache Size = Daily Active Data × Hot Data Percentage
```

**Example: URL Shortener Cache**
```
Given:
- Total URLs: 1 billion
- Daily active URLs: 20% = 200 million
- URL mapping size: 500 bytes (short URL + long URL + metadata)
- Target cache hit rate: 80%

Hot data (following 80/20 rule):
To achieve 80% cache hit, cache top 20% of daily active data:
200M × 20% = 40 million URLs

Cache memory required:
40M × 500 bytes = 20 GB

With overhead (serialization, data structure):
20 GB × 1.5 = 30 GB

For redundancy (2 cache nodes):
30 GB × 2 = 60 GB total
```

**Cache Sizing Guidelines:**
```
Scenario                      | Cache Size
------------------------------|------------------
Session data                  | Sessions × 10 KB
User profiles                 | Active users × 5 KB
Recent posts/content          | Daily content × object size
Query results                 | Common queries × result size
```

---

## Common Estimation Patterns

### Pattern 1: Read-Heavy System (100:1)
```
Example: News Feed, Content Platform

Read QPS >> Write QPS

Design implications:
- Heavy caching (CDN, Redis)
- Read replicas for database
- Denormalized data for fast reads
- Eventual consistency acceptable
```

### Pattern 2: Write-Heavy System (1:1 or 1:10)
```
Example: Logging, Analytics, IoT

Write QPS >= Read QPS

Design implications:
- Append-only storage (Kafka, Cassandra)
- Async writes, batch processing
- Sharding for write distribution
- LSM-tree based databases
```

### Pattern 3: Mixed System
```
Example: Social Media (post + view)

Read:Write varies by feature

Design implications:
- CQRS (Command Query Responsibility Segregation)
- Different storage for reads vs writes
- Event sourcing
```

---

## Server Estimation

### Compute Requirements

**Rule of Thumb:**
```
A single server can handle:
- 10K-50K simple API requests/second
- 1K-5K database queries/second
- 100-500 complex operations/second
```

**Example: API Server Sizing**
```
Given:
- Peak QPS: 100,000
- Each server handles: 10,000 QPS

Servers needed:
100,000 ÷ 10,000 = 10 servers

With 50% headroom:
10 × 1.5 = 15 servers

With redundancy (N+2):
15 + 2 = 17 servers
```

### Database Server Estimation

```
Single Database Server Capacity (typical):
- Simple reads: 10K-50K QPS
- Simple writes: 1K-10K QPS
- Complex queries: 100-1K QPS

Sharding calculation:
If you need 50K write QPS and each shard handles 5K:
Shards needed = 50K ÷ 5K = 10 shards
```

---

## Estimation Worksheet Template

```
=== SYSTEM ESTIMATION WORKSHEET ===

1. TRAFFIC
   DAU: _____________
   Actions per user: _____________ reads, _____________ writes

   Daily requests:
   - Reads:  DAU × reads/user = _____________
   - Writes: DAU × writes/user = _____________

   Average QPS:
   - Reads:  daily reads ÷ 86,400 = _____________
   - Writes: daily writes ÷ 86,400 = _____________

   Peak QPS (× 3):
   - Reads:  _____________ × 3 = _____________
   - Writes: _____________ × 3 = _____________

2. STORAGE
   Objects created per day: _____________
   Size per object: _____________
   Retention period: _____________

   Daily storage: objects × size = _____________
   Total storage: daily × retention = _____________
   With replication (×3): _____________

3. BANDWIDTH
   Average request size: _____________
   Daily data transfer: requests × size = _____________
   Average bandwidth: transfer ÷ 86,400 = _____________
   Peak bandwidth: _____________ × 3 = _____________

4. CACHE
   Daily active data: _____________
   Hot data (20%): _____________
   Cache size: hot data × object size = _____________

5. SERVERS
   QPS per server: _____________
   Servers needed: peak QPS ÷ QPS per server = _____________
   With overhead (×1.5): _____________
```

---

## Interview Tips

### Do's
- Round numbers for easy mental math
- State assumptions clearly
- Show your work step by step
- Double-check with sanity checks
- Use 80/20 rule for quick estimates

### Don'ts
- Don't try to be too precise
- Don't forget about peak traffic
- Don't ignore replication/redundancy
- Don't forget metadata and indexes
- Don't skip sanity checks

### Sanity Checks
```
Ask yourself:
- Does this number seem reasonable?
- Compare to known systems
- Is the cost feasible?
- Are we in the right order of magnitude?
```

### Time Management
```
In a 45-minute interview:
- Spend 3-5 minutes on estimation
- Get key numbers (QPS, storage)
- Don't over-optimize this section
- Move on once you have ballpark figures
```

---

## Worked Examples

### Example 1: URL Shortener
See [Case Studies: URL Shortener](../10-case-studies/url-shortener.md)

### Example 2: Twitter
See [Case Studies: Twitter Feed](../10-case-studies/twitter-feed.md)

---

## Next Steps

After estimation:
1. → [API Design](../03-api-design/) - Design endpoints for your scale
2. → [Data Model](../04-data-model/) - Choose storage based on requirements
3. → [High-Level Design](../05-high-level-design/) - Architect the system
