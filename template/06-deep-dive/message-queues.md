# Message Queues Deep Dive

Understanding asynchronous messaging patterns for building scalable, decoupled systems.

---

## Why Message Queues?

```
Benefits:
  - Decouple services (sender doesn't wait for receiver)
  - Handle traffic spikes (buffer during peaks)
  - Reliable delivery (messages persist until processed)
  - Enable async processing (background jobs)
  - Scale consumers independently

Use Cases:
  - Background job processing (emails, reports)
  - Event-driven architecture
  - Microservice communication
  - Order processing pipelines
  - Log aggregation
  - Real-time notifications
```

---

## Messaging Patterns

### 1. Point-to-Point (Queue)

```
Each message consumed by exactly one consumer.

Producer ───> [ Message Queue ] ───> Consumer

Multiple Consumers (Competing):
                              ┌───> Consumer A
Producer ───> [ Queue ] ──────┼───> Consumer B
                              └───> Consumer C

Each message goes to ONE consumer (work distribution)

Use Cases:
  - Task/work queues
  - Job processing
  - Order processing
  - Email sending
```

### 2. Publish/Subscribe (Topic)

```
Messages broadcast to all subscribers.

                              ┌───> Subscriber A
Publisher ───> [ Topic ] ─────┼───> Subscriber B
                              └───> Subscriber C

All subscribers receive ALL messages

Use Cases:
  - Event notifications
  - Real-time updates
  - Cache invalidation
  - Logging/monitoring
```

### 3. Request/Reply

```
Async request with correlation for response.

Requester ───> [ Request Queue ] ───> Responder
    │                                     │
    │          [ Reply Queue ]            │
    └──────────────<──────────────────────┘

Implementation:
  - Include reply-to queue in message
  - Include correlation ID
  - Responder sends to reply queue

Use Cases:
  - Async API calls
  - Long-running operations
  - Remote procedure calls
```

---

## Delivery Guarantees

### At-Most-Once

```
Message may be lost, but never duplicated.

Flow:
  1. Producer sends message
  2. Consumer receives message
  3. Message deleted immediately
  4. Consumer processes (may fail)

If consumer fails: Message lost

Use when:
  - Data loss is acceptable
  - Real-time metrics
  - Non-critical notifications
```

### At-Least-Once

```
Message delivered one or more times.

Flow:
  1. Producer sends message
  2. Consumer receives message
  3. Consumer processes
  4. Consumer acknowledges
  5. Message deleted after ACK

If consumer fails before ACK: Message redelivered

Requires:
  - Idempotent consumers
  - Deduplication logic

Most common guarantee for reliable systems.
```

### Exactly-Once

```
Message delivered exactly one time.

Implementation approaches:
  1. Transactional outbox pattern
  2. Idempotency keys
  3. Two-phase commit (complex)

In practice:
  - Usually "effectively once"
  - At-least-once + idempotency
  - Kafka supports exactly-once for streams
```

---

## Apache Kafka Deep Dive

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Kafka Cluster                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Topic: orders                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │   │
│  │  │Partition │  │Partition │  │Partition │              │   │
│  │  │    0     │  │    1     │  │    2     │              │   │
│  │  └──────────┘  └──────────┘  └──────────┘              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                        │
│  │ Broker 1│  │ Broker 2│  │ Broker 3│                        │
│  └─────────┘  └─────────┘  └─────────┘                        │
└─────────────────────────────────────────────────────────────────┘

Key Concepts:
  - Topic: Category of messages (like database table)
  - Partition: Ordered, immutable log
  - Broker: Kafka server
  - Consumer Group: Set of consumers sharing load
  - Offset: Position in partition
```

### Partitioning

```
Producer decides partition:
  - By key (hash): Same key → same partition → ordering
  - Round-robin: Even distribution

Example:
  Key = user_id ensures all events for a user go to same partition

  User A's events → Partition 0 (ordered)
  User B's events → Partition 1 (ordered)
  User C's events → Partition 0 (ordered)

Partition Count:
  - More partitions = more parallelism
  - But more overhead
  - Recommended: 10-100 per topic for most cases
```

### Consumer Groups

```
┌──────────────────────────────────────────────────────────┐
│                    Topic: orders                          │
│   ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│   │ Partition 0│  │ Partition 1│  │ Partition 2│        │
│   └──────┬─────┘  └──────┬─────┘  └──────┬─────┘        │
└──────────│───────────────│───────────────│───────────────┘
           │               │               │
           ▼               ▼               ▼
    ┌────────────────────────────────────────────┐
    │           Consumer Group: processing        │
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
    │  │Consumer A│  │Consumer B│  │Consumer C│ │
    │  │(P0)      │  │(P1)      │  │(P2)      │ │
    │  └──────────┘  └──────────┘  └──────────┘ │
    └────────────────────────────────────────────┘

Rules:
  - Each partition → at most one consumer in group
  - Max consumers = number of partitions
  - Adding consumers → rebalance
```

### Kafka vs Traditional Queues

```
Aspect              │ Kafka                    │ RabbitMQ/SQS
────────────────────┼──────────────────────────┼──────────────────
Model               │ Log-based                │ Queue-based
Message Retention   │ Configurable (days/size) │ Until consumed
Consumer Offset     │ Consumer managed         │ Queue managed
Replay              │ Yes (seek to offset)     │ No
Ordering            │ Per partition            │ FIFO (limited)
Throughput          │ Very high (1M+ msg/sec)  │ High (100K msg/sec)
Use Case            │ Event streaming          │ Task queues
```

---

## RabbitMQ Deep Dive

### Exchange Types

```
1. Direct Exchange:
   Routes by exact routing key match

   Exchange ──routing_key="orders"──> Queue orders
           ──routing_key="payments"──> Queue payments

2. Fanout Exchange:
   Broadcasts to all bound queues

   Exchange ───> Queue A
           ───> Queue B
           ───> Queue C

3. Topic Exchange:
   Pattern matching on routing key

   Routing Key: "order.created.usa"

   Pattern "order.*.*"     → matches
   Pattern "order.created.*" → matches
   Pattern "*.*.usa"       → matches

4. Headers Exchange:
   Routes by message headers (key-value)
```

### Message Flow

```
┌──────────┐    ┌──────────────┐    ┌─────────┐    ┌──────────┐
│ Producer │───>│   Exchange   │───>│  Queue  │───>│ Consumer │
└──────────┘    └──────────────┘    └─────────┘    └──────────┘
     │                 │                 │               │
     │            Routing            Buffering      Processing
     │                                   │               │
     └───────────────────────────────────┘               │
                    Acknowledgment (ACK) <───────────────┘
```

### Reliability Features

```
Publisher Confirms:
  - Broker confirms receipt
  - Async or sync

Consumer Acknowledgments:
  - Manual ACK after processing
  - NACK with requeue on failure
  - Prefetch limit (QoS)

Message Persistence:
  - Durable queues (survive restart)
  - Persistent messages (written to disk)

Dead Letter Exchange:
  - Failed messages routed here
  - For debugging and recovery
```

---

## Message Design Patterns

### 1. Outbox Pattern

```
Ensures message is sent if and only if DB transaction commits.

┌─────────────────────────────────────────────────────────┐
│                    Transaction                           │
│  1. Update business tables                              │
│  2. Insert into outbox table                            │
│  COMMIT                                                  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              Background Worker (CDC or polling)          │
│  1. Read from outbox                                    │
│  2. Publish to message queue                            │
│  3. Mark as sent                                        │
└─────────────────────────────────────────────────────────┘

Benefits:
  - Atomic with database changes
  - No distributed transactions
```

### 2. Saga Pattern

```
Coordinate long-running transactions across services.

Order Saga:
  1. Create Order (Order Service)
  2. Reserve Inventory (Inventory Service)
  3. Process Payment (Payment Service)
  4. Ship Order (Shipping Service)

Compensation on failure:
  Payment fails → Release inventory → Cancel order

Implementation:
  - Choreography: Events trigger next step
  - Orchestration: Central coordinator
```

### 3. Dead Letter Queue

```
Handle failed messages gracefully.

┌─────────┐    ┌─────────────┐    ┌──────────┐
│  Queue  │───>│  Consumer   │───>│ Process  │
└─────────┘    └──────┬──────┘    └────┬─────┘
                      │                 │
                 On failure        Success
                      │                 │
                      ▼                 ▼
              ┌──────────────┐    ┌──────────┐
              │  Dead Letter │    │   ACK    │
              │    Queue     │    └──────────┘
              └──────────────┘

DLQ Processing:
  - Manual review
  - Automated retry after fix
  - Alerting on DLQ growth
```

---

## Message Queue Comparison

```
Feature           │ Kafka       │ RabbitMQ    │ SQS         │ Redis Pub/Sub
──────────────────┼─────────────┼─────────────┼─────────────┼──────────────
Throughput        │ Very High   │ High        │ High        │ Very High
Ordering          │ Per partition│ Per queue  │ FIFO option │ None
Persistence       │ Yes (log)   │ Yes         │ Yes         │ No
Replay            │ Yes         │ No          │ No          │ No
Consumer Groups   │ Yes         │ Yes         │ Limited     │ No
Exactly-Once      │ Yes*        │ With effort │ With effort │ No
Managed Option    │ Confluent   │ CloudAMQP   │ Native AWS  │ ElastiCache
Use Case          │ Streaming   │ Tasks       │ AWS native  │ Real-time
```

---

## Scaling Strategies

### Producer Scaling

```
Batch messages:
  - Group messages before sending
  - Reduces network overhead
  - Kafka: linger.ms, batch.size

Async sending:
  - Don't wait for acknowledgment
  - Fire and forget (at-most-once)
  - Or collect futures (at-least-once)
```

### Consumer Scaling

```
Horizontal scaling:
  - Add more consumer instances
  - Kafka: Add partitions first
  - RabbitMQ: More consumers on queue

Prefetch/Batch:
  - Fetch multiple messages at once
  - Process in parallel
  - Batch commits/acks
```

---

## Monitoring and Operations

### Key Metrics

```
Metric              │ Alert Threshold         │ Action
────────────────────┼─────────────────────────┼──────────────────
Consumer Lag        │ > 10,000 messages       │ Scale consumers
Queue Depth         │ > 100,000 messages      │ Investigate backlog
DLQ Size            │ > 0                     │ Check failures
Processing Time     │ > SLA                   │ Optimize or scale
Error Rate          │ > 1%                    │ Investigate failures
```

### Operational Concerns

```
Backpressure:
  - Slow consumers → queue grows
  - Solution: Scale consumers, rate limit producers

Poison Messages:
  - Messages that always fail
  - Solution: Dead letter queue, max retries

Ordering Requirements:
  - May limit parallelism
  - Solution: Partition by entity
```

---

## Interview Tips

### Questions to Ask

```
1. What's the message rate?
   → Sizing and technology choice

2. What's the acceptable latency?
   → Real-time vs batch processing

3. Can we lose messages?
   → Delivery guarantee needed

4. Do messages need ordering?
   → Affects partitioning strategy

5. What happens if consumer is slow?
   → Backpressure handling
```

### Key Points to Discuss

```
✓ Why async vs sync communication
✓ Delivery guarantee chosen
✓ Ordering requirements
✓ Consumer scaling strategy
✓ Failure handling (DLQ)
✓ Idempotency
```

---

## Next Steps

1. → [Microservices Patterns](microservices-patterns.md) - Service communication
2. → [Fault Tolerance](fault-tolerance.md) - Reliability patterns
3. → [Case Studies](../10-case-studies/) - See queues in practice
