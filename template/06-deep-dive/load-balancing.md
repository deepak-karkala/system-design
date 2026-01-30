# Load Balancing Deep Dive

Comprehensive guide to distributing traffic across servers for high availability and performance.

---

## Load Balancer Types

### Layer 4 (Transport Layer)

```
Operates at TCP/UDP level.

Client ───TCP───> Load Balancer ───TCP───> Server

Characteristics:
  - Routes based on IP and port only
  - Very fast (no content inspection)
  - No application awareness
  - Simple configuration

Use Cases:
  - High-throughput applications
  - Non-HTTP protocols
  - TCP/UDP traffic
  - Network-level distribution

Examples: AWS NLB, HAProxy (TCP mode), IPVS
```

### Layer 7 (Application Layer)

```
Operates at HTTP/HTTPS level.

Client ───HTTPS───> Load Balancer ───HTTP───> Server
                         │
                    Inspects:
                    - URL path
                    - Headers
                    - Cookies
                    - Body (rare)

Characteristics:
  - Content-based routing
  - SSL termination
  - Request modification
  - Caching possible

Use Cases:
  - Web applications
  - API routing
  - A/B testing
  - Canary deployments

Examples: AWS ALB, NGINX, HAProxy (HTTP mode), Envoy
```

---

## Load Balancing Algorithms

### Round Robin

```
Distributes requests sequentially.

Request 1 ───> Server A
Request 2 ───> Server B
Request 3 ───> Server C
Request 4 ───> Server A (back to start)

Pros:
  ✓ Simple implementation
  ✓ Even distribution
  ✓ No state required

Cons:
  ✗ Ignores server capacity
  ✗ Ignores current load
  ✗ Ignores request complexity

Best for:
  - Homogeneous servers
  - Similar request costs
  - Stateless applications
```

### Weighted Round Robin

```
Accounts for server capacity.

Servers:
  A (weight=5): Handles 5 of every 8 requests
  B (weight=2): Handles 2 of every 8 requests
  C (weight=1): Handles 1 of every 8 requests

Sequence: A, A, A, B, A, B, C, A, ...

Use when:
  - Servers have different capacities
  - Gradual migration (new server low weight)
```

### Least Connections

```
Routes to server with fewest active connections.

Current State:
  Server A: 10 connections
  Server B: 5 connections  ← Next request goes here
  Server C: 8 connections

Pros:
  ✓ Adapts to server load
  ✓ Handles varying request durations

Cons:
  ✗ Requires connection tracking
  ✗ May overload recovering server

Best for:
  - Long-lived connections
  - Varying request complexity
  - Stateful protocols
```

### Least Response Time

```
Routes to server with fastest response + fewest connections.

Considers:
  - Active connections
  - Average response time
  - Recent performance

Pros:
  ✓ Performance-aware
  ✓ Avoids slow servers

Cons:
  ✗ More complex tracking
  ✗ May oscillate
```

### IP Hash

```
Same client IP always routes to same server.

hash(client_ip) mod num_servers = server_index

Client 1.2.3.4 → Always Server A
Client 5.6.7.8 → Always Server B

Pros:
  ✓ Session affinity without cookies
  ✓ Cache efficiency

Cons:
  ✗ Uneven if traffic skewed
  ✗ Changes when servers added/removed
```

### Consistent Hashing

```
Minimizes redistribution when servers change.

Hash Ring:
     0°
      │
   A──┼──B
      │
     180°

Adding server C:
  - Only keys between B and C move
  - Other mappings unchanged

Virtual nodes:
  - Each server has multiple positions
  - More even distribution
  - Smoother rebalancing

Best for:
  - Caching layers
  - Distributed databases
  - Stateful services
```

---

## Health Checks

### Types

```
1. TCP Health Check:
   - Checks if port is open
   - Simplest, fastest
   - No application awareness

   health_check:
     type: tcp
     port: 8080
     interval: 10s
     timeout: 5s

2. HTTP Health Check:
   - Makes HTTP request
   - Checks status code
   - Can verify response body

   health_check:
     type: http
     path: /health
     expected_status: 200
     interval: 30s
     timeout: 10s

3. Custom Health Check:
   - Run custom script
   - Complex logic
   - Resource-intensive
```

### Health Check Design

```
Endpoint: GET /health

Response (healthy):
{
  "status": "healthy",
  "checks": {
    "database": "up",
    "cache": "up",
    "disk": "ok"
  }
}

Response (unhealthy):
{
  "status": "unhealthy",
  "checks": {
    "database": "down",  // Critical dependency
    "cache": "up",
    "disk": "ok"
  }
}

Best Practices:
  ✓ Fast response (<1s)
  ✓ Check critical dependencies
  ✓ Different endpoints for liveness/readiness
  ✓ Don't check non-critical services
```

### Liveness vs Readiness

```
Liveness: "Is the process alive?"
  - Check: Process running, not deadlocked
  - Failure action: Restart container
  - Should be quick and simple

Readiness: "Can it handle traffic?"
  - Check: Warmup complete, dependencies ready
  - Failure action: Stop routing traffic
  - More comprehensive checks

Kubernetes example:
  livenessProbe:
    httpGet:
      path: /healthz
      port: 8080
    initialDelaySeconds: 10
    periodSeconds: 10

  readinessProbe:
    httpGet:
      path: /ready
      port: 8080
    initialDelaySeconds: 5
    periodSeconds: 5
```

---

## Advanced Features

### SSL Termination

```
Client ──HTTPS──> LB ──HTTP──> Backend

Benefits:
  ✓ Offload CPU from backends
  ✓ Centralized certificate management
  ✓ Simpler backend configuration

Considerations:
  - Traffic LB→Backend is unencrypted
  - Use private network
  - Or re-encrypt (SSL bridging)
```

### Sticky Sessions (Session Affinity)

```
Same client always routed to same backend.

Methods:
1. Cookie-based:
   Set-Cookie: SERVERID=server-a

2. IP-based:
   hash(client_ip) → server

When to use:
  - Session stored on server
  - Websocket connections
  - In-memory cache per user

Better alternative:
  - Externalize session (Redis)
  - Stateless backends
```

### Connection Draining

```
Graceful server removal.

1. Mark server as "draining"
2. Stop sending new connections
3. Wait for existing to complete
4. Remove server

Configuration:
  connection_draining:
    enabled: true
    timeout: 300s  # Max wait time
```

### Rate Limiting

```
Prevent abuse at load balancer level.

rate_limit:
  requests_per_second: 1000
  burst: 100
  by: client_ip

Response when exceeded:
  HTTP 429 Too Many Requests
  Retry-After: 60
```

---

## High Availability

### Active-Passive

```
┌──────────────┐
│  Active LB   │ ←── All traffic
└──────┬───────┘
       │
    Heartbeat
       │
┌──────▼───────┐
│  Passive LB  │ ←── Standby
└──────────────┘

Failover:
  1. Active fails
  2. Passive detects (heartbeat timeout)
  3. Passive takes over VIP
  4. Traffic flows to new active

Pro: Simple
Con: Passive wastes resources
```

### Active-Active

```
┌──────────────┐     ┌──────────────┐
│     LB 1     │     │     LB 2     │
└──────┬───────┘     └──────┬───────┘
       │                    │
       └────────┬───────────┘
                │
        DNS Round Robin
         or Anycast

Both handle traffic:
  - DNS returns multiple IPs
  - Anycast routes to nearest
  - Global server load balancing

Pro: Full utilization, no waste
Con: More complex
```

---

## Global Load Balancing

### DNS-Based

```
┌─────────────────────────────────────────────────────────────┐
│                      DNS (Route 53)                          │
│  example.com →                                               │
│    US users  → us.example.com (1.1.1.1)                     │
│    EU users  → eu.example.com (2.2.2.2)                     │
│    APAC users → ap.example.com (3.3.3.3)                    │
└─────────────────────────────────────────────────────────────┘

Routing Policies:
  - Geolocation: Route by user location
  - Latency: Route to lowest latency region
  - Weighted: Percentage-based distribution
  - Failover: Primary/secondary
```

### Anycast

```
Same IP advertised from multiple locations.
BGP routes to nearest location.

┌───────────────────────────────────────────────────────────┐
│                     IP: 1.2.3.4                           │
│  ┌────────┐         ┌────────┐         ┌────────┐       │
│  │ US-East│         │ EU-West│         │  APAC  │       │
│  │ 1.2.3.4│         │ 1.2.3.4│         │ 1.2.3.4│       │
│  └────────┘         └────────┘         └────────┘       │
└───────────────────────────────────────────────────────────┘

User in France → Routed to EU-West automatically

Pros:
  ✓ Automatic nearest routing
  ✓ DDoS resilience
  ✓ Simple client (single IP)

Used by: Cloudflare, Google, major CDNs
```

---

## Load Balancer Selection

```
Requirement              │ L4 (NLB)  │ L7 (ALB)  │ Software
─────────────────────────┼───────────┼───────────┼───────────
HTTP routing             │     ✗     │     ✓     │     ✓
WebSocket                │     ✓     │     ✓     │     ✓
SSL termination          │     ✗     │     ✓     │     ✓
Content-based routing    │     ✗     │     ✓     │     ✓
Ultra-low latency        │     ✓     │     ✗     │     ✓
Millions of connections  │     ✓     │     ✗     │     ✓
Cost                     │   Lower   │  Higher   │  Flexible
Managed                  │     ✓     │     ✓     │     ✗
```

---

## Interview Tips

### Questions to Ask

```
1. What protocol is being used?
   → Determines L4 vs L7

2. Is content-based routing needed?
   → Requires L7

3. What's the expected connection count?
   → Sizing and type

4. What's the geographic distribution?
   → Global LB consideration

5. Is session affinity needed?
   → Affects algorithm choice
```

### Key Points to Discuss

```
✓ Layer 4 vs Layer 7 trade-offs
✓ Algorithm selection rationale
✓ Health check design
✓ High availability approach
✓ SSL termination decision
✓ Sticky session alternatives
```

---

## Next Steps

1. → [Fault Tolerance](fault-tolerance.md) - Reliability patterns
2. → [Security](security.md) - Security considerations
3. → [Case Studies](../10-case-studies/) - See LB in practice
