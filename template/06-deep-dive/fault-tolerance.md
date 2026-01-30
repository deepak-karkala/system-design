# Fault Tolerance & Reliability

Building systems that survive failures gracefully.

---

## Core Concepts

```
Fault: Something goes wrong (disk fails, network drops)
Error: Fault causes incorrect behavior
Failure: System stops providing service

Goal: Prevent faults from becoming failures

Key Metrics:
  MTBF: Mean Time Between Failures
  MTTR: Mean Time To Recovery
  Availability = MTBF / (MTBF + MTTR)
```

---

## Redundancy Patterns

### Active-Passive (Hot Standby)

```
┌────────────┐         ┌────────────┐
│   Active   │ ──────> │  Passive   │
│  (Primary) │  Sync   │ (Standby)  │
└─────┬──────┘         └─────┬──────┘
      │                      │
      │ Traffic              │ No traffic
      ▼                      │
   Clients                   │
                             │
      On Active Failure:     │
      ─────────────────>     ▼
                          Takes over

Characteristics:
  - Standby is idle (waste)
  - Simple failover
  - Some downtime during failover

Use: Databases, stateful services
```

### Active-Active

```
┌────────────┐         ┌────────────┐
│  Active 1  │         │  Active 2  │
└─────┬──────┘         └─────┬──────┘
      │                      │
      │ Traffic              │ Traffic
      ▼                      ▼
   ┌────────────────────────────┐
   │       Load Balancer        │
   └─────────────┬──────────────┘
                 │
              Clients

Characteristics:
  - All resources utilized
  - No failover delay
  - More complex (state sync)

Use: Stateless services, web servers
```

### N+1 Redundancy

```
For N required capacity, run N+1 instances.

Example: Need capacity for 90 req/s
  - Each server handles 30 req/s
  - Run 4 servers (3+1)
  - One can fail without impact

┌───┐ ┌───┐ ┌───┐ ┌───┐
│ A │ │ B │ │ C │ │ D │  ← D is the +1
└───┘ └───┘ └───┘ └───┘
```

---

## Failure Detection

### Health Checks

```
Active Health Checks:
  - Load balancer pings servers
  - Remove unhealthy from rotation
  - Configurable interval and threshold

Passive Health Checks:
  - Monitor real traffic errors
  - Detect failures faster
  - May have false positives

Configuration:
  interval: 10s          # How often to check
  timeout: 5s            # Max wait for response
  healthy_threshold: 2   # Consecutive success
  unhealthy_threshold: 3 # Consecutive failure
```

### Heartbeat Systems

```
Node 1 ──heartbeat──> Coordinator
Node 2 ──heartbeat──> Coordinator
Node 3 ──heartbeat──> Coordinator

Coordinator:
  - Expects heartbeat every N seconds
  - Missing heartbeat = potentially failed
  - Trigger failover after threshold

Challenge: Distinguishing slow from dead
```

### Phi Accrual Detector

```
Adaptive failure detection.

Instead of binary alive/dead:
  - Calculate probability of failure
  - Based on historical heartbeat timing
  - Adapts to network conditions

Used by: Cassandra, Akka
```

---

## Resilience Patterns

### Circuit Breaker

```
Prevent cascading failures by failing fast.

States:
  ┌─────────┐    Failures > threshold    ┌──────────┐
  │ Closed  │ ─────────────────────────> │   Open   │
  └────┬────┘                            └────┬─────┘
       │                                      │
       │ Requests pass                        │ Requests fail immediately
       │                                      │
       │                            Timeout   │
       │         ┌────────────┐ <─────────────┘
       └───────> │ Half-Open  │
                 └──────┬─────┘
                        │
         Test request   │  Success: Close
         fails: Open    ▼  Failure: Open

Implementation:
  circuit_breaker = CircuitBreaker(
      failure_threshold=5,
      recovery_timeout=30,
      half_open_requests=3
  )

  result = circuit_breaker.execute(call_external_service)

Libraries: Hystrix, Resilience4j, Polly
```

### Retry with Backoff

```
Retry failed requests with increasing delay.

Attempt 1: Immediate
Attempt 2: Wait 1 second
Attempt 3: Wait 2 seconds
Attempt 4: Wait 4 seconds
Attempt 5: Wait 8 seconds (max)

Exponential backoff with jitter:
  delay = min(max_delay, base_delay * 2^attempt + random_jitter)

def retry_with_backoff(func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return func()
        except RetryableError:
            delay = min(30, (2 ** attempt) + random.uniform(0, 1))
            time.sleep(delay)
    raise MaxRetriesExceeded()

Important:
  - Only retry idempotent operations
  - Add jitter to prevent thundering herd
  - Set max retries to avoid infinite loops
```

### Bulkhead

```
Isolate components to prevent total failure.

┌─────────────────────────────────────────────────────────┐
│                     Application                          │
├─────────────────┬─────────────────┬─────────────────────┤
│   Pool A        │   Pool B        │   Pool C            │
│   (10 threads)  │   (10 threads)  │   (10 threads)      │
│   [Service A]   │   [Service B]   │   [Service C]       │
└─────────────────┴─────────────────┴─────────────────────┘

If Service A is slow:
  - Only Pool A exhausted
  - Pools B and C unaffected
  - System partially available

Types:
  - Thread pool isolation
  - Connection pool isolation
  - Process isolation
  - Container/pod isolation
```

### Timeout

```
Set time limits on operations.

Hierarchy of timeouts:
  Client request:    30s
    └── Service A:   10s
        └── DB:       5s
        └── Cache:    1s

Rules:
  - Inner timeout < outer timeout
  - Include margin for processing
  - Handle TimeoutException gracefully

def call_with_timeout(func, timeout_seconds):
    try:
        return func(timeout=timeout_seconds)
    except TimeoutError:
        return fallback_response()
```

### Fallback

```
Provide degraded functionality on failure.

Strategies:
  1. Cached Response:
     if service.call() fails:
         return cache.get_stale()

  2. Default Value:
     if recommendation.call() fails:
         return popular_items()

  3. Degraded Response:
     if full_profile.call() fails:
         return basic_profile_from_db()

  4. Queue for Later:
     if payment.call() fails:
         queue.add(payment_request)
         return "Processing..."
```

---

## Data Reliability

### Replication

```
Synchronous Replication:
  Client ──write──> Primary ──sync──> Replica
         <──ack───         <──ack───

  - Write confirmed after replica ack
  - No data loss
  - Higher latency

Asynchronous Replication:
  Client ──write──> Primary ──async──> Replica
         <──ack───

  - Write confirmed immediately
  - Possible data loss on primary failure
  - Lower latency

Quorum:
  W + R > N for consistency
  Example: N=3, W=2, R=2
```

### Backup Strategies

```
Full Backup:
  - Complete copy of data
  - Time-consuming
  - Weekly/monthly

Incremental Backup:
  - Only changes since last backup
  - Fast
  - Daily

Continuous Backup (Point-in-Time):
  - Transaction log shipping
  - Minimal data loss
  - RPO in seconds

3-2-1 Rule:
  - 3 copies of data
  - 2 different storage types
  - 1 offsite location
```

---

## Chaos Engineering

```
Intentionally inject failures to test resilience.

Principles:
  1. Start with steady state hypothesis
  2. Vary real-world events
  3. Run experiments in production
  4. Automate experiments

Experiments:
  - Kill random instances
  - Inject latency
  - Simulate network partition
  - Fill disk space
  - CPU stress

Tools:
  - Chaos Monkey (Netflix)
  - Gremlin
  - Litmus Chaos
  - Chaos Mesh
```

---

## Graceful Degradation

```
Prioritize core functionality during stress.

Example: E-commerce during peak traffic

Normal mode:
  ✓ Product browsing
  ✓ Personalized recommendations
  ✓ Full search
  ✓ Reviews
  ✓ Checkout

Degraded mode (high load):
  ✓ Product browsing
  ✓ Checkout
  ✗ Recommendations (static)
  ✗ Full search (basic only)
  ✗ Reviews (cached)

Implementation:
  - Feature flags
  - Load shedding
  - Priority queues
  - Circuit breakers
```

---

## Incident Response

### Runbook Template

```
Incident: [Service Name] Down

Symptoms:
  - Error rate > 10%
  - Latency P99 > 5s
  - Health checks failing

Diagnosis Steps:
  1. Check service health: kubectl get pods
  2. Check logs: kubectl logs [pod]
  3. Check database: SELECT 1
  4. Check dependencies: curl http://dep/health

Mitigation:
  1. Scale up: kubectl scale --replicas=10
  2. Rollback: kubectl rollout undo
  3. Enable fallback: feature_flag.enable('fallback')
  4. Block bad actor: iptables -A INPUT -s [IP] -j DROP

Escalation:
  - P1: Page on-call immediately
  - P2: Slack alert, 15 min response
  - P3: Ticket, next business day
```

### Post-Mortem

```
What happened?
  - Timeline of events
  - Impact (duration, users affected)

Root cause?
  - 5 whys analysis
  - Actual cause, not symptoms

What went well?
  - Detection time
  - Response effectiveness

What went wrong?
  - Gaps in monitoring
  - Missing runbooks

Action items:
  - Fix root cause
  - Improve detection
  - Update runbooks
  - Add tests
```

---

## Interview Tips

### Questions to Ask

```
1. What's the availability requirement?
   → Determines redundancy level

2. What's acceptable recovery time?
   → Active-passive vs active-active

3. What operations are idempotent?
   → Safe to retry

4. What's the blast radius of failures?
   → Bulkhead design

5. Is there a fallback behavior?
   → Graceful degradation
```

### Key Points to Discuss

```
✓ Single points of failure eliminated
✓ Failure detection mechanism
✓ Retry strategy (backoff, jitter)
✓ Circuit breaker placement
✓ Fallback behaviors
✓ Monitoring and alerting
✓ Recovery procedures
```

---

## Next Steps

1. → [Security](security.md) - Security patterns
2. → [Observability](observability.md) - Monitoring systems
3. → [Case Studies](../10-case-studies/) - See patterns in practice
