# URL Shortener (TinyURL, Bit.ly)

Design a URL shortening service like TinyURL or Bit.ly.

---

## 1. Requirements

### Functional Requirements
```
Core Features:
  1. Given a long URL, generate a short URL
  2. Given a short URL, redirect to original URL
  3. Optional: Custom short URLs
  4. Optional: Analytics (click counts)

Out of Scope:
  - User accounts
  - Rate limiting (discuss briefly)
  - Link expiration (mention)
```

### Non-Functional Requirements
```
Scale:
  - 100M URLs created per month
  - 10B redirects per month
  - Read:Write ratio = 100:1

Performance:
  - Redirect latency: < 100ms
  - URL creation: < 500ms

Availability:
  - 99.9% uptime

Durability:
  - URLs should persist for 5 years
```

---

## 2. Estimation

### Traffic
```
Write (URL creation):
  100M / month = 100M / (30 × 24 × 3600) ≈ 40 URLs/second
  Peak: 40 × 3 = 120 URLs/second

Read (Redirects):
  10B / month = 10B / (30 × 24 × 3600) ≈ 4,000 redirects/second
  Peak: 4,000 × 3 = 12,000 redirects/second
```

### Storage
```
Per URL:
  - Short URL: 7 chars = 7 bytes
  - Long URL: avg 200 bytes
  - Created at: 8 bytes
  - Metadata: 50 bytes
  Total: ~265 bytes

5 years of URLs:
  100M × 12 × 5 = 6 billion URLs
  6B × 265 bytes ≈ 1.6 TB

With indexes and overhead: ~3 TB
```

### Bandwidth
```
Read:
  4,000 req/s × 265 bytes ≈ 1 MB/s

Write:
  40 req/s × 265 bytes ≈ 10 KB/s

Minimal bandwidth requirements.
```

---

## 3. API Design

```
POST /urls
  Request: {
    "long_url": "https://example.com/very/long/path",
    "custom_alias": "my-link"  // optional
  }
  Response: {
    "short_url": "https://tiny.url/abc1234",
    "long_url": "https://example.com/very/long/path",
    "created_at": "2024-01-15T10:30:00Z"
  }

GET /{short_code}
  Response: HTTP 301 Redirect
  Location: https://example.com/very/long/path

GET /urls/{short_code}/stats  (optional)
  Response: {
    "short_url": "https://tiny.url/abc1234",
    "clicks": 1500,
    "created_at": "2024-01-15T10:30:00Z"
  }
```

---

## 4. High-Level Design

```
                              ┌─────────────┐
                              │   Client    │
                              └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │     CDN     │
                              │  (optional) │
                              └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │    Load     │
                              │  Balancer   │
                              └──────┬──────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
               ┌────▼────┐     ┌─────▼────┐    ┌─────▼────┐
               │   URL   │     │   URL    │    │   URL    │
               │ Service │     │ Service  │    │ Service  │
               └────┬────┘     └────┬─────┘    └────┬─────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
               ┌────▼────┐    ┌─────▼────┐    ┌─────▼────┐
               │  Cache  │    │ Database │    │   Key    │
               │ (Redis) │    │(Cassandra│    │Generator │
               └─────────┘    │ or MySQL)│    │ Service  │
                              └──────────┘    └──────────┘

Data Flow (Create):
  1. Client sends long URL
  2. Service gets unique key from Key Generator
  3. Stores mapping in Database
  4. Updates Cache
  5. Returns short URL

Data Flow (Redirect):
  1. Client requests short URL
  2. Service checks Cache
  3. If miss, checks Database
  4. Returns 301 redirect
```

---

## 5. Deep Dive: Key Generation

### Challenge: Generate Unique Short Codes

#### Option 1: Hash-Based (MD5/SHA)
```
short_code = base62(hash(long_url))[:7]

Problems:
  - Collisions possible
  - Same URL → same code (might want different)
  - Need collision handling

Collision handling:
  while exists(short_code):
      short_code = base62(hash(long_url + timestamp))[:7]
```

#### Option 2: Counter-Based (Recommended)
```
Key Generation Service:
  - Maintains a counter
  - Converts counter to base62

Base62: [a-zA-Z0-9] = 62 characters
7 characters = 62^7 = 3.5 trillion unique codes

┌─────────────────────────────────────────────────────────┐
│               Key Generation Service                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Pre-generate keys in batches:                          │
│                                                          │
│  ┌─────────────┐                                        │
│  │ Key Range   │                                        │
│  │ Service     │ → Assigns ranges to app servers        │
│  └─────────────┘                                        │
│                                                          │
│  Server A: [1-1000000]                                  │
│  Server B: [1000001-2000000]                            │
│  Server C: [2000001-3000000]                            │
│                                                          │
│  Each server generates keys from its range              │
│  No coordination needed until range exhausted           │
│                                                          │
└─────────────────────────────────────────────────────────┘

def generate_key(counter):
    base62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    result = ""
    while counter > 0:
        result = base62[counter % 62] + result
        counter //= 62
    return result.zfill(7)

Example:
  Counter 1 → "0000001"
  Counter 62 → "0000010"
  Counter 1000000 → "4c92" (padded to 7 chars)
```

---

## 6. Database Design

### Option 1: SQL (MySQL/PostgreSQL)
```sql
CREATE TABLE urls (
    id BIGINT PRIMARY KEY,
    short_code VARCHAR(10) UNIQUE NOT NULL,
    long_url VARCHAR(2048) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    click_count BIGINT DEFAULT 0
);

CREATE INDEX idx_short_code ON urls(short_code);

Pros: ACID, familiar
Cons: Scaling challenges at very high scale
```

### Option 2: NoSQL (Cassandra/DynamoDB) - Recommended
```
Table: urls
Partition Key: short_code

{
    "short_code": "abc1234",
    "long_url": "https://example.com/...",
    "created_at": "2024-01-15T10:30:00Z",
    "click_count": 1500
}

Pros:
  - Horizontal scaling
  - High write throughput
  - Simple key-value access pattern

Cons:
  - No complex queries
  - Eventual consistency
```

---

## 7. Caching Strategy

```
Cache: Redis

Strategy: Cache-Aside (Lazy Loading)

def redirect(short_code):
    # Check cache first
    long_url = cache.get(short_code)

    if long_url is None:
        # Cache miss - check database
        long_url = database.get(short_code)
        if long_url:
            cache.set(short_code, long_url, ttl=24_hours)

    return redirect(long_url)

Cache sizing:
  - Hot URLs (20%): 20% of 6B = 1.2B URLs
  - Size per URL: 265 bytes
  - Cache size: 1.2B × 265 ≈ 300 GB

Redis Cluster with 4-5 nodes should suffice.
```

---

## 8. Key Trade-offs

```
Trade-off 1: Key Generation
  Chose: Counter-based with range allocation
  Over: Hash-based
  Because: No collisions, predictable, simpler

Trade-off 2: Database
  Chose: Cassandra (NoSQL)
  Over: PostgreSQL
  Because: Better horizontal scaling, simple access pattern

Trade-off 3: Consistency
  Chose: Eventual consistency
  Over: Strong consistency
  Because: Brief inconsistency acceptable, better availability

Trade-off 4: Redirect Code
  Chose: 301 (Permanent Redirect)
  Over: 302 (Temporary Redirect)
  Because: Browser caching reduces server load
  Note: Use 302 if analytics is critical (301 cached by browser)
```

---

## 9. Additional Considerations

### Rate Limiting
```
Prevent abuse:
  - Per IP: 10 creates/minute
  - Per user (if auth): 100 creates/minute

Implementation:
  - Token bucket in Redis
  - Return 429 when exceeded
```

### Analytics
```
Click tracking:
  - Async update to avoid redirect latency
  - Send to Kafka → Analytics Service → Time-series DB

  def redirect(short_code):
      # Fire and forget analytics
      kafka.send("clicks", {"code": short_code, "timestamp": now})
      return redirect(long_url)
```

### Link Expiration
```
Options:
  1. TTL in database
  2. Background job to clean expired
  3. Check on read (lazy deletion)
```

---

## 10. Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    URL SHORTENER ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Components:                                                     │
│    • Load Balancer (HAProxy/ALB)                                │
│    • URL Service (stateless, horizontally scaled)               │
│    • Key Generator Service (range-based allocation)             │
│    • Cache (Redis Cluster)                                      │
│    • Database (Cassandra)                                       │
│    • Optional: Kafka + Analytics                                │
│                                                                  │
│  Key Metrics:                                                   │
│    • 40 writes/sec, 4,000 reads/sec                            │
│    • 3 TB storage (5 years)                                     │
│    • < 100ms redirect latency                                   │
│                                                                  │
│  Key Decisions:                                                 │
│    • Counter-based key generation                               │
│    • NoSQL for horizontal scaling                               │
│    • Heavy caching for read performance                         │
│    • 301 redirects for browser caching                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interview Tips for This Problem

```
Key points to hit:
  1. Key generation is the main challenge - discuss options
  2. Read-heavy (100:1) - emphasize caching
  3. Simple data model - NoSQL works well
  4. Discuss trade-offs for redirect codes (301 vs 302)
  5. Mention analytics as extension

Common follow-ups:
  - How to handle custom aliases?
  - How to prevent abuse?
  - How to do analytics without affecting latency?
  - How to handle hot URLs (viral links)?
```
