# Distributed Rate Limiter

Design a distributed rate limiting system.

---

## 1. Requirements

### Functional Requirements
```
Core Features:
  1. Limit requests per user/IP/API key
  2. Support multiple rate limit rules (per second, minute, hour)
  3. Return rate limit headers in responses
  4. Support different limits for different endpoints
  5. Allow burst traffic within limits

Out of Scope:
  - Request queuing
  - Dynamic rule updates via API
  - Cost-based rate limiting
```

### Non-Functional Requirements
```
Scale:
  - 1M requests per second
  - 100M unique clients
  - Global deployment (multi-region)

Performance:
  - Rate check latency: < 1ms (p99)
  - Minimal impact on request latency

Availability:
  - 99.99% uptime
  - Graceful degradation (allow if rate limiter fails)

Accuracy:
  - Allow small margin of error (±1-5%)
  - Eventual consistency across regions acceptable
```

---

## 2. Estimation

### Traffic
```
Rate limit checks:
  1M requests/second
  Each request = 1 rate limit check (minimum)
  Multiple rules = multiple checks per request

Redis operations:
  2-4 operations per check
  = 2-4M operations/second on Redis
```

### Storage
```
Per client state:
  • Counter: 8 bytes
  • Timestamp: 8 bytes
  • Metadata: ~100 bytes

100M clients × 120 bytes ≈ 12 GB

With multiple windows (per second, minute, hour):
  100M × 3 windows × 120 bytes ≈ 36 GB
```

---

## 3. API Design

```
Rate Limit Configuration:

PUT /rate-limits/rules
  Request: {
    "rules": [
      {
        "id": "api_default",
        "match": {"path": "/api/*"},
        "limits": [
          {"window": "1s", "max": 10},
          {"window": "1m", "max": 100},
          {"window": "1h", "max": 1000}
        ]
      },
      {
        "id": "auth_strict",
        "match": {"path": "/api/auth/*"},
        "limits": [
          {"window": "1m", "max": 5},
          {"window": "1h", "max": 20}
        ]
      }
    ]
  }

Rate Limit Check (Internal):

POST /rate-limit/check
  Request: {
    "client_id": "user123",
    "rule_id": "api_default"
  }
  Response: {
    "allowed": true,
    "remaining": 95,
    "reset_at": 1705312260
  }

Response Headers (to API clients):

X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705312260

When rate limited:
  HTTP 429 Too Many Requests
  Retry-After: 45
```

---

## 4. High-Level Design

```
                              ┌─────────────┐
                              │   Clients   │
                              └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │    Load     │
                              │  Balancer   │
                              └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │ API Gateway │
                              │ (Rate Limit │
                              │  Middleware)│
                              └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │ Rate Limit  │
                              │   Service   │
                              └──────┬──────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           │                         │                         │
     ┌─────▼─────┐            ┌──────▼─────┐            ┌─────▼─────┐
     │   Redis   │            │   Redis    │            │   Redis   │
     │  Cluster  │            │   Cluster  │            │   Cluster │
     │ (Region A)│            │  (Region B)│            │ (Region C)│
     └───────────┘            └────────────┘            └───────────┘

Alternative: Local counter + Sync

     ┌─────────────┐       ┌─────────────┐
     │ API Server  │       │ API Server  │
     │  + Local    │       │  + Local    │
     │   Counter   │       │   Counter   │
     └──────┬──────┘       └──────┬──────┘
            │                     │
            └──────────┬──────────┘
                       │
                ┌──────▼──────┐
                │   Central   │
                │    Redis    │
                └─────────────┘
```

---

## 5. Deep Dive: Rate Limiting Algorithms

### Algorithm Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                    RATE LIMITING ALGORITHMS                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Fixed Window Counter                                        │
│  ─────────────────────────                                      │
│     • Count requests in fixed time windows                      │
│     • Simple to implement                                       │
│     • Problem: Burst at window boundaries                       │
│                                                                  │
│     Window 1        Window 2                                    │
│     [----100----]   [----100----]                               │
│              ↑ 100 here + 100 here = 200 in short period        │
│                                                                  │
│  2. Sliding Window Log                                          │
│  ─────────────────────                                          │
│     • Store timestamp of each request                           │
│     • Count requests in sliding window                          │
│     • Accurate but memory-intensive                             │
│                                                                  │
│     Timestamps: [t1, t2, t3, t4, t5]                           │
│     Count requests where timestamp > (now - window)             │
│                                                                  │
│  3. Sliding Window Counter (Recommended)                        │
│  ───────────────────────────────────────                        │
│     • Approximation of sliding window                           │
│     • Two fixed windows with weighted average                   │
│     • Good balance of accuracy and efficiency                   │
│                                                                  │
│     Count = prev_count × (1 - elapsed/window) + curr_count      │
│                                                                  │
│  4. Token Bucket                                                │
│  ──────────────                                                 │
│     • Bucket holds tokens, refills at constant rate             │
│     • Request consumes token                                    │
│     • Allows burst up to bucket size                            │
│                                                                  │
│     Bucket: [○○○○○○○○○○] capacity=10, refill=1/sec             │
│     Request takes 1 token if available                          │
│                                                                  │
│  5. Leaky Bucket                                                │
│  ──────────────                                                 │
│     • Queue with fixed processing rate                          │
│     • Smooths out bursts                                        │
│     • Requests may be queued or dropped                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Sliding Window Counter Implementation

```python
def is_allowed(client_id, limit, window_seconds):
    now = time.time()
    current_window = int(now // window_seconds)
    prev_window = current_window - 1

    # Keys for current and previous window
    curr_key = f"rate:{client_id}:{current_window}"
    prev_key = f"rate:{client_id}:{prev_window}"

    # Get counts
    pipe = redis.pipeline()
    pipe.get(prev_key)
    pipe.get(curr_key)
    prev_count, curr_count = pipe.execute()

    prev_count = int(prev_count or 0)
    curr_count = int(curr_count or 0)

    # Calculate position in current window
    elapsed = now - (current_window * window_seconds)
    weight = (window_seconds - elapsed) / window_seconds

    # Weighted count
    total = prev_count * weight + curr_count

    if total >= limit:
        return False, int(limit - total)

    # Increment current window
    pipe = redis.pipeline()
    pipe.incr(curr_key)
    pipe.expire(curr_key, window_seconds * 2)
    pipe.execute()

    return True, int(limit - total - 1)
```

### Token Bucket Implementation

```python
def is_allowed_token_bucket(client_id, capacity, refill_rate):
    """
    capacity: Maximum tokens (allows burst)
    refill_rate: Tokens added per second
    """
    key = f"bucket:{client_id}"
    now = time.time()

    # Lua script for atomic operation
    lua_script = """
    local key = KEYS[1]
    local capacity = tonumber(ARGV[1])
    local refill_rate = tonumber(ARGV[2])
    local now = tonumber(ARGV[3])
    local requested = tonumber(ARGV[4])

    local data = redis.call('HMGET', key, 'tokens', 'last_update')
    local tokens = tonumber(data[1]) or capacity
    local last_update = tonumber(data[2]) or now

    -- Calculate tokens to add
    local elapsed = now - last_update
    local new_tokens = math.min(capacity, tokens + (elapsed * refill_rate))

    -- Check if request allowed
    if new_tokens >= requested then
        new_tokens = new_tokens - requested
        redis.call('HMSET', key, 'tokens', new_tokens, 'last_update', now)
        redis.call('EXPIRE', key, 3600)
        return {1, new_tokens}
    else
        return {0, new_tokens}
    end
    """

    allowed, remaining = redis.eval(lua_script, 1, key, capacity, refill_rate, now, 1)
    return allowed == 1, remaining
```

---

## 6. Deep Dive: Distributed Rate Limiting

### Challenges

```
┌─────────────────────────────────────────────────────────────────┐
│                    DISTRIBUTED CHALLENGES                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Problem 1: Race Conditions                                     │
│  ──────────────────────────                                     │
│    Multiple servers increment counter simultaneously            │
│    → May exceed limit                                           │
│                                                                  │
│    Solution: Atomic operations                                  │
│    • Use Redis INCR (atomic)                                    │
│    • Lua scripts for complex operations                         │
│                                                                  │
│  Problem 2: Multi-Region Sync                                   │
│  ────────────────────────────                                   │
│    User can hit different regions                               │
│    → Limits not enforced globally                               │
│                                                                  │
│    Solutions:                                                   │
│    a) Single global Redis (high latency)                        │
│    b) Regional Redis + periodic sync (eventual consistency)     │
│    c) Sticky sessions to single region                          │
│                                                                  │
│  Problem 3: Redis Failure                                       │
│  ────────────────────────                                       │
│    If Redis down, no rate limiting                              │
│    → System vulnerable                                          │
│                                                                  │
│    Solutions:                                                   │
│    a) Redis Cluster with replicas                               │
│    b) Local fallback counter                                    │
│    c) Fail open (allow) vs fail closed (deny)                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Multi-Region Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MULTI-REGION DESIGN                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Option 1: Single Global Redis                                  │
│  ─────────────────────────────                                  │
│                                                                  │
│     Region A          Region B          Region C                │
│     [Servers] ───────────────────────> [Global Redis]           │
│                         ↑                                       │
│                    High latency                                 │
│                    (100-200ms)                                  │
│                                                                  │
│  Option 2: Local Redis + Sync (Recommended)                     │
│  ──────────────────────────────────────────                     │
│                                                                  │
│     Region A              Region B              Region C        │
│     [Servers]             [Servers]             [Servers]       │
│        │                     │                     │            │
│     [Redis A] ←──sync───→ [Redis B] ←──sync───→ [Redis C]      │
│                                                                  │
│     Each region enforces local limit                            │
│     Periodic sync (every 5-10 seconds)                          │
│     Global limit = sum of regional allocations                  │
│                                                                  │
│     Example:                                                    │
│       Global limit: 1000/min                                    │
│       Region A allocation: 400/min                              │
│       Region B allocation: 400/min                              │
│       Region C allocation: 200/min                              │
│                                                                  │
│  Option 3: Token Bucket with Central Pool                       │
│  ────────────────────────────────────────                       │
│                                                                  │
│     Each region has local tokens                                │
│     Periodically replenish from central pool                    │
│     Borrow tokens if local pool exhausted                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Regional Allocation

```python
class RegionalRateLimiter:
    def __init__(self, global_limit, num_regions):
        self.global_limit = global_limit
        self.base_allocation = global_limit // num_regions

        # Dynamic allocation based on traffic
        self.current_allocation = self.base_allocation
        self.borrowed = 0

    def check_and_borrow(self, client_id):
        allowed, remaining = self.local_check(client_id)

        if not allowed and self.can_borrow():
            # Try to borrow from central pool
            borrowed = self.borrow_from_central(10)
            self.borrowed += borrowed
            if borrowed > 0:
                return self.local_check(client_id)

        return allowed, remaining

    def borrow_from_central(self, amount):
        # Atomic operation on central Redis
        script = """
        local available = redis.call('GET', 'central_pool') or 0
        if available >= amount then
            redis.call('DECRBY', 'central_pool', amount)
            return amount
        end
        return 0
        """
        return central_redis.eval(script, 0, amount)

    def return_unused(self):
        # Return unused quota periodically
        unused = self.current_allocation - self.used_this_window
        if unused > 0:
            central_redis.incrby('central_pool', unused)
```

---

## 7. Deep Dive: Implementation Patterns

### API Gateway Integration

```python
# Middleware for API Gateway
class RateLimitMiddleware:
    def __init__(self, rate_limiter):
        self.rate_limiter = rate_limiter
        self.rules = self.load_rules()

    async def process_request(self, request):
        # Identify client
        client_id = self.get_client_id(request)

        # Get applicable rule
        rule = self.get_rule(request.path)

        # Check all windows
        for limit_config in rule.limits:
            allowed, remaining = await self.rate_limiter.is_allowed(
                client_id=client_id,
                limit=limit_config.max,
                window=limit_config.window
            )

            if not allowed:
                return self.rate_limited_response(
                    limit=limit_config.max,
                    remaining=0,
                    reset_at=self.calculate_reset(limit_config.window)
                )

        # Add headers and continue
        request.add_header('X-RateLimit-Limit', rule.limits[0].max)
        request.add_header('X-RateLimit-Remaining', remaining)
        return None  # Continue to next middleware

    def get_client_id(self, request):
        # Priority: API key > User ID > IP
        if api_key := request.headers.get('X-API-Key'):
            return f"key:{api_key}"
        if user_id := request.user_id:
            return f"user:{user_id}"
        return f"ip:{request.client_ip}"

    def rate_limited_response(self, limit, remaining, reset_at):
        return Response(
            status=429,
            headers={
                'X-RateLimit-Limit': limit,
                'X-RateLimit-Remaining': remaining,
                'X-RateLimit-Reset': reset_at,
                'Retry-After': reset_at - int(time.time())
            },
            body={'error': 'Rate limit exceeded'}
        )
```

### Redis Cluster Configuration

```
Redis Cluster for high availability:

3 masters + 3 replicas (minimum)

Master 1 → Replica 1
Master 2 → Replica 2
Master 3 → Replica 3

Data sharding:
  • CRC16(client_id) % 16384 = slot
  • Each master owns ~5500 slots

Failover:
  • Replica promotes to master if master fails
  • < 1 second failover with Sentinel

Configuration:
  maxmemory 10gb
  maxmemory-policy volatile-lru
  appendonly yes
  appendfsync everysec
```

---

## 8. Database Design

### Rate Limit Rules (PostgreSQL)

```sql
CREATE TABLE rate_limit_rules (
    rule_id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    match_path VARCHAR(200),
    match_method VARCHAR(10),
    match_headers JSONB,
    priority INT DEFAULT 0,  -- Higher = checked first
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE rate_limit_configs (
    config_id UUID PRIMARY KEY,
    rule_id UUID REFERENCES rate_limit_rules(rule_id),
    window_seconds INT NOT NULL,
    max_requests INT NOT NULL,
    burst_size INT  -- For token bucket
);

CREATE INDEX idx_rules_enabled ON rate_limit_rules(enabled, priority DESC);
```

### Redis Data Structures

```
Counter-based (sliding window):
  Key: rate:{client_id}:{window_id}
  Value: Integer count
  TTL: 2 × window_seconds

Token bucket:
  Key: bucket:{client_id}
  Value: Hash { tokens: int, last_update: timestamp }
  TTL: 1 hour (refreshed on access)

Sliding window log:
  Key: log:{client_id}
  Value: Sorted set { timestamp: timestamp }
  TTL: window_seconds
```

---

## 9. Key Trade-offs

```
Trade-off 1: Accuracy vs Performance
  Chose: Allow 5% margin of error
  Because: Exact global counting too expensive
  Implementation: Regional allocation with sync

Trade-off 2: Fail Open vs Fail Closed
  Chose: Fail open (allow requests if Redis down)
  Because: Availability > security for most cases
  Mitigation: Local fallback counter, alerts

Trade-off 3: Algorithm Choice
  Chose: Sliding window counter
  Because: Good balance of accuracy and memory
  Alternative: Token bucket for APIs needing burst

Trade-off 4: Synchronization Frequency
  Chose: Sync every 10 seconds
  Because: Balance consistency and overhead
  Impact: Up to 10s of over-quota allowed
```

---

## 10. Handling Edge Cases

### Sudden Traffic Spike

```
Problem: Traffic spikes beyond capacity

Solutions:
  1. Adaptive limits:
     - Reduce limits automatically under pressure
     - Protect system health

  2. Priority queuing:
     - Premium clients get priority
     - Degrade gracefully for free tier

  3. Circuit breaker:
     - If Redis overwhelmed, use local-only limiting
     - More permissive but prevents cascade failure
```

### Clock Skew

```
Problem: Different servers have different time

Impact:
  - Window boundaries misaligned
  - Counts may be off

Solutions:
  1. Use Redis server time:
     TIME command returns server timestamp
     All rate limit calculations use same clock

  2. NTP synchronization:
     All servers sync to same NTP source
     Ensure < 1 second drift
```

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    RATE LIMITER ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Request Flow:                                                  │
│    Request → API Gateway → Rate Limit Check → Service           │
│                                                                  │
│  Rate Limit Check:                                              │
│    1. Extract client identifier                                 │
│    2. Match request to rule                                     │
│    3. Check all windows (second, minute, hour)                  │
│    4. Allow or reject                                           │
│                                                                  │
│  Storage:                                                       │
│    • Redis Cluster: Counters, tokens (primary)                  │
│    • PostgreSQL: Rules configuration                            │
│    • Local memory: Fallback counters                            │
│                                                                  │
│  Key Design Decisions:                                          │
│    • Sliding window counter algorithm                           │
│    • Regional Redis with periodic sync                          │
│    • Fail open for availability                                 │
│    • Lua scripts for atomic operations                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interview Tips

```
Key points to hit:
  1. Explain different algorithms and trade-offs
  2. Address distributed challenges (race conditions, multi-region)
  3. Redis atomic operations (INCR, Lua scripts)
  4. Failure handling strategy
  5. Response headers (standard X-RateLimit-*)

Common follow-ups:
  - How to handle Redis failure?
  - How to rate limit across multiple data centers?
  - How to implement dynamic rate limits?
  - How to handle authenticated vs unauthenticated users differently?
```
