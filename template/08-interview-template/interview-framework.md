# System Design Interview Framework

A structured approach to ace system design interviews in 45-60 minutes.

---

## Interview Timeline (45 minutes)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     45-MINUTE INTERVIEW BREAKDOWN                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Phase 1: Requirements & Clarification               5 min      │   │
│  │ • Functional requirements                                       │   │
│  │ • Non-functional requirements (scale, latency)                  │   │
│  │ • Scope boundaries                                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Phase 2: Estimation                                 5 min      │   │
│  │ • Traffic (QPS)                                                 │   │
│  │ • Storage                                                       │   │
│  │ • Bandwidth                                                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Phase 3: API Design                                 5 min      │   │
│  │ • Key endpoints                                                 │   │
│  │ • Request/response format                                       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Phase 4: High-Level Design                          10 min     │   │
│  │ • Draw components                                               │   │
│  │ • Explain data flow                                             │   │
│  │ • Identify key decisions                                        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Phase 5: Deep Dive                                  15 min     │   │
│  │ • Database design                                               │   │
│  │ • Scaling strategies                                            │   │
│  │ • Specific challenges                                           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Phase 6: Wrap-up                                    5 min      │   │
│  │ • Trade-offs                                                    │   │
│  │ • Future improvements                                           │   │
│  │ • Questions                                                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Requirements (5 min)

### Functional Requirements

```
Ask:
  1. "Who are the users of this system?"
  2. "What are the core features we need to support?"
  3. "Are there any features explicitly out of scope?"

Document:
  ✓ User types (customers, admins, etc.)
  ✓ Core user flows (2-3 main features)
  ✓ Explicit scope boundaries

Example (Twitter):
  Users: Regular users, verified users
  Core features:
    - Post tweets (text, images)
    - View home timeline
    - Follow/unfollow users
  Out of scope:
    - Direct messages
    - Trending topics
    - Ads
```

### Non-Functional Requirements

```
Ask:
  1. "What's the expected scale? (DAU, total users)"
  2. "What latency is acceptable?"
  3. "Is availability or consistency more important?"
  4. "Any specific compliance requirements?"

Document:
  ✓ Scale: DAU, total users, growth
  ✓ Latency: P99 target
  ✓ Availability: Target SLA
  ✓ Consistency: Strong vs eventual

Example (Twitter):
  - 300M DAU, 500M total users
  - Timeline load < 500ms
  - 99.9% availability
  - Eventual consistency for timeline OK
```

---

## Phase 2: Estimation (5 min)

### Quick Calculation Template

```
Traffic:
  DAU × actions/user/day = daily operations
  Daily operations ÷ 86,400 = QPS
  QPS × 3 = Peak QPS

  Example:
    300M DAU × 10 reads = 3B reads/day
    3B ÷ 86,400 ≈ 35,000 QPS
    Peak: ~100,000 QPS

Storage:
  Objects × size × retention

  Example:
    300M tweets/day × 500 bytes = 150 GB/day
    5 years = 150 GB × 365 × 5 = 274 TB

Key ratios:
  Read:Write ratio (e.g., 100:1 for read-heavy)
```

### Estimation Cheat Sheet

```
Quick References:
  1M requests/day ≈ 12 QPS
  1KB × 1M = 1 GB
  Seconds in day ≈ 86,400 ≈ 100,000 (for easy math)
```

---

## Phase 3: API Design (5 min)

### Define Key Endpoints

```
Format:
  METHOD /resource
  Request: { ... }
  Response: { ... }

Example (Twitter):

  POST /tweets
  Request: { "content": "Hello world", "media_ids": [...] }
  Response: { "tweet_id": "123", "created_at": "..." }

  GET /timeline?cursor=xxx&limit=20
  Response: { "tweets": [...], "next_cursor": "yyy" }

  POST /users/{user_id}/follow
  Response: { "success": true }
```

### Key Considerations

```
Mention briefly:
  - Authentication (JWT, OAuth)
  - Rate limiting
  - Pagination (cursor-based for feeds)
  - Idempotency (for writes)
```

---

## Phase 4: High-Level Design (10 min)

### Draw the Architecture

```
Start with standard components:

Clients → CDN → Load Balancer → API Gateway → Services
                                                 │
                                    ┌────────────┼────────────┐
                                    │            │            │
                                    ▼            ▼            ▼
                                 Cache       Database    Message Queue
                                                              │
                                                           Workers

Add system-specific components as needed.
```

### Explain Data Flow

```
Walk through 1-2 key user flows:

"Let me walk through posting a tweet:"
  1. Client sends POST to API Gateway
  2. Gateway authenticates and routes to Tweet Service
  3. Tweet Service validates, stores in DB
  4. Event published to fan-out queue
  5. Fan-out workers update follower timelines
  6. Response returned to client

Use numbers from estimation to validate design.
```

---

## Phase 5: Deep Dive (15 min)

### Database Design

```
Topics to cover:
  1. Schema for main entities
  2. Database choice (SQL vs NoSQL)
  3. Indexing strategy
  4. Sharding approach

Example:
  "For tweets, I'd use a NoSQL store like Cassandra because:
   - Write-heavy workload
   - Need horizontal scaling
   - Don't need complex joins

   Partition key: user_id
   Clustering key: timestamp (descending)

   This allows efficient queries for user's tweets."
```

### Scaling Strategies

```
Address based on requirements:

Read scaling:
  - Read replicas
  - Caching (Redis)
  - CDN for static content

Write scaling:
  - Sharding
  - Async processing
  - Write-behind cache

Geographic scaling:
  - Multi-region
  - Edge computing
  - Global load balancing
```

### System-Specific Challenges

```
Every system has unique challenges. Examples:

Twitter: Timeline fan-out
  - Push vs Pull model
  - Hybrid for celebrities

URL Shortener: Key generation
  - Counter vs random
  - Collision handling

Chat: Presence and delivery
  - WebSockets
  - Offline message queue

Video: Transcoding and delivery
  - Async processing
  - Adaptive streaming
```

---

## Phase 6: Wrap-up (5 min)

### Discuss Trade-offs

```
Structure:
  "We chose X over Y because of Z."
  "The trade-off is..."

Example:
  "We chose eventual consistency for timelines because:
   - Latency is critical for user experience
   - Slight delay in seeing tweets is acceptable
   - Strong consistency would require coordination

   The trade-off is users might see tweets slightly delayed."
```

### Future Improvements

```
Mention 2-3 things you'd add with more time:
  - Monitoring and alerting
  - Analytics pipeline
  - Additional features
  - Further optimization

Example:
  "With more time, I'd add:
   - Real-time analytics for trending topics
   - ML-based feed ranking
   - A/B testing infrastructure"
```

---

## Interview Signals

### What Interviewers Look For

```
Strong Signals:
  ✓ Asks clarifying questions
  ✓ Drives the conversation
  ✓ Explains trade-offs
  ✓ Uses numbers to validate
  ✓ Considers failure modes
  ✓ Demonstrates depth in areas of expertise

Weak Signals:
  ✗ Jumps to solution without requirements
  ✗ Only shallow coverage
  ✗ Can't discuss alternatives
  ✗ Ignores scale implications
  ✗ Doesn't consider operations
```

### Senior vs Staff Expectations

```
Senior (L5/E5):
  - Solid fundamentals
  - Good trade-off discussion
  - Can design standard systems
  - Asks good questions

Staff (L6/E6):
  - Deep expertise in 1-2 areas
  - Proactively identifies edge cases
  - Considers organizational impact
  - Drives to optimal solution

Principal (L7+):
  - System-wide thinking
  - Novel problem solving
  - Industry context
  - Long-term evolution
```

---

## Common Mistakes

```
1. Not clarifying requirements
   Fix: Always spend first 5 minutes on requirements

2. Jumping to complex solutions
   Fix: Start simple, add complexity as needed

3. Not drawing diagrams
   Fix: Always draw, even if simple

4. Ignoring scale implications
   Fix: Use numbers from estimation throughout

5. Not discussing trade-offs
   Fix: Every decision has pros and cons

6. Talking without listening
   Fix: Check in with interviewer regularly

7. Getting stuck on one area
   Fix: Time-box each section
```

---

## Quick Reference Card

```
┌────────────────────────────────────────────────────────┐
│                 INTERVIEW QUICK REFERENCE               │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Requirements Questions:                               │
│    • Who are the users?                               │
│    • What are the core features?                      │
│    • What's the scale?                                │
│    • What's the latency requirement?                  │
│                                                        │
│  Estimation Quick Math:                               │
│    • 1M/day = 12 QPS                                  │
│    • 1KB × 1M = 1 GB                                  │
│    • Peak = Average × 3                               │
│                                                        │
│  Always Draw:                                         │
│    • Clients → LB → Services → DB                    │
│    • Add caching, queues as needed                    │
│                                                        │
│  Key Questions to Address:                            │
│    • How does it scale?                               │
│    • What happens on failure?                         │
│    • What are the trade-offs?                         │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## Next Steps

1. → [Question Bank](question-bank.md) - Questions to ask
2. → [Evaluation Criteria](evaluation-criteria.md) - How you're evaluated
3. → [Case Studies](../10-case-studies/) - Practice problems
