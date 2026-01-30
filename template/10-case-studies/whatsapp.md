# WhatsApp / Messaging System

Design a real-time messaging system like WhatsApp or Messenger.

---

## 1. Requirements

### Functional Requirements
```
Core Features:
  1. Send/receive messages (1:1 and group)
  2. Real-time message delivery
  3. Message delivery status (sent, delivered, read)
  4. Online/offline presence
  5. Media sharing (images, videos, files)

Out of Scope:
  - Voice/video calls
  - Stories/Status
  - End-to-end encryption details
  - Message reactions
```

### Non-Functional Requirements
```
Scale:
  - 2B users total
  - 500M DAU
  - 100B messages per day
  - Average user in 10 group chats

Performance:
  - Message delivery: < 100ms (same region)
  - Online status update: < 1 second
  - Media upload: Background, resumable

Availability:
  - 99.99% uptime

Consistency:
  - Messages must be delivered in order (per conversation)
  - No message loss (at-least-once delivery)
```

---

## 2. Estimation

### Traffic
```
Messages:
  100B messages/day ÷ 86,400 ≈ 1.16M messages/second
  Peak (2x): 2.3M messages/second

Connections:
  500M DAU × 30% concurrent ≈ 150M concurrent connections
```

### Storage
```
Message storage:
  Average message: 100 bytes
  100B × 100 bytes = 10 TB/day

  Keep 30 days on hot storage: 300 TB
  Archive older messages: Cold storage

Media:
  20% messages have media
  100B × 20% × 200 KB average = 4 PB/day
```

### Bandwidth
```
Messages:
  1.16M messages/sec × 100 bytes = 116 MB/second

Media (assuming 10% actively downloading):
  100K concurrent downloads × 1 MB/s = 100 GB/second
  CDN handles most of this
```

---

## 3. API Design

```
WebSocket Events (Real-time):

// Client → Server
{
  "type": "message",
  "conversation_id": "conv123",
  "content": "Hello!",
  "client_msg_id": "client_uuid_123"
}

{
  "type": "typing",
  "conversation_id": "conv123",
  "is_typing": true
}

{
  "type": "ack",
  "message_ids": ["msg456", "msg457"],
  "status": "read"
}

// Server → Client
{
  "type": "message",
  "message_id": "msg456",
  "conversation_id": "conv123",
  "sender_id": "user789",
  "content": "Hello!",
  "timestamp": "2024-01-15T10:30:00Z"
}

{
  "type": "status_update",
  "message_id": "msg456",
  "status": "delivered"
}

REST APIs (Fallback/Historical):

GET /conversations
GET /conversations/{id}/messages?before=timestamp&limit=50
POST /media/upload
GET /users/{id}/presence
```

---

## 4. High-Level Design

```
                              ┌─────────────┐
                              │   Clients   │
                              │(Mobile/Web) │
                              └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │    Load     │
                              │  Balancer   │
                              └──────┬──────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
              ┌─────▼─────┐   ┌──────▼─────┐   ┌─────▼─────┐
              │ WebSocket │   │   REST     │   │  Media    │
              │  Gateway  │   │   API      │   │  Service  │
              └─────┬─────┘   └──────┬─────┘   └─────┬─────┘
                    │                │               │
                    │          ┌─────▼─────┐        │
                    │          │  Message  │        │
                    │          │  Service  │        │
                    │          └─────┬─────┘        │
                    │                │               │
         ┌──────────┴────┐     ┌─────▼─────┐   ┌───▼────┐
         │               │     │  Presence │   │  Blob  │
    ┌────▼────┐    ┌─────▼───┐ │  Service  │   │ Storage│
    │ Session │    │ Message │ └───────────┘   │  (S3)  │
    │  Store  │    │  Queue  │                 └────────┘
    │ (Redis) │    │ (Kafka) │
    └─────────┘    └────┬────┘
                        │
                   ┌────▼────┐
                   │ Message │
                   │   DB    │
                   └─────────┘
```

---

## 5. Deep Dive: WebSocket Connection Management

### Connection Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONNECTION MANAGEMENT                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Challenge: 150M concurrent WebSocket connections                │
│                                                                  │
│  Solution: Distributed WebSocket Gateway                         │
│                                                                  │
│  ┌─────────┐     ┌─────────────────────────────────┐            │
│  │ Client  │────>│     Load Balancer (L4)          │            │
│  └─────────┘     │  (Sticky sessions by user_id)   │            │
│                  └───────────────┬─────────────────┘            │
│                                  │                               │
│            ┌─────────────────────┼─────────────────────┐        │
│            │                     │                     │        │
│       ┌────▼────┐          ┌─────▼────┐          ┌────▼────┐   │
│       │   WS    │          │    WS    │          │   WS    │   │
│       │Gateway 1│          │ Gateway 2│          │Gateway 3│   │
│       │ 50K conn│          │ 50K conn │          │ 50K conn│   │
│       └────┬────┘          └────┬─────┘          └────┬────┘   │
│            │                    │                     │         │
│            └────────────────────┼─────────────────────┘         │
│                                 │                                │
│                          ┌──────▼──────┐                        │
│                          │   Redis     │                        │
│                          │  Pub/Sub    │                        │
│                          └─────────────┘                        │
│                                                                  │
│  Each gateway server:                                           │
│    • Maintains 50-100K connections                              │
│    • Stores connection mapping in Redis                         │
│    • Subscribes to user channels                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Message Routing

```
┌─────────────────────────────────────────────────────────────────┐
│                    MESSAGE ROUTING                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User A (Gateway 1) sends message to User B (Gateway 3)         │
│                                                                  │
│  1. Gateway 1 receives message from User A                      │
│                                                                  │
│  2. Message Service processes:                                  │
│     - Validate message                                          │
│     - Store in database                                         │
│     - Publish to Kafka topic                                    │
│                                                                  │
│  3. Find User B's connection:                                   │
│     Redis: GET user:B:gateway → "gateway3"                      │
│                                                                  │
│  4. Route options:                                              │
│                                                                  │
│     Option A: Redis Pub/Sub                                     │
│       PUBLISH user:B:messages {message}                         │
│       Gateway 3 subscribed, delivers to User B                  │
│                                                                  │
│     Option B: Direct Gateway Communication                      │
│       Gateway 1 → Gateway 3 via internal RPC                    │
│       Lower latency, more complex                               │
│                                                                  │
│  5. If User B offline:                                          │
│     - Store in pending messages queue                           │
│     - Send push notification                                    │
│     - Deliver when User B connects                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Connection State Management

```python
class ConnectionManager:
    def __init__(self):
        self.local_connections = {}  # user_id → websocket
        self.redis = Redis()

    def on_connect(self, user_id, websocket):
        # Store locally
        self.local_connections[user_id] = websocket

        # Register in Redis
        self.redis.hset(f"user:{user_id}:connection", {
            "gateway": self.gateway_id,
            "connected_at": time.time()
        })

        # Subscribe to user's channel
        self.redis.subscribe(f"user:{user_id}:messages")

        # Deliver pending messages
        self.deliver_pending_messages(user_id)

    def on_disconnect(self, user_id):
        # Remove local connection
        del self.local_connections[user_id]

        # Update Redis (don't delete immediately for reconnection)
        self.redis.hset(f"user:{user_id}:connection", {
            "status": "disconnected",
            "disconnected_at": time.time()
        })

        # Unsubscribe
        self.redis.unsubscribe(f"user:{user_id}:messages")

    def send_to_user(self, user_id, message):
        # Check if connected locally
        if user_id in self.local_connections:
            self.local_connections[user_id].send(message)
            return True

        # Check if connected to another gateway
        conn_info = self.redis.hgetall(f"user:{user_id}:connection")
        if conn_info and conn_info["status"] == "connected":
            # Publish to user's channel
            self.redis.publish(f"user:{user_id}:messages", message)
            return True

        # User offline
        return False
```

---

## 6. Deep Dive: Message Delivery Guarantees

### Message States

```
┌─────────────────────────────────────────────────────────────────┐
│                    MESSAGE DELIVERY STATES                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────┐   ┌──────────┐   ┌───────────┐   ┌──────────┐     │
│  │  Sent   │──>│ Delivered│──>│   Read    │   │ Failed   │     │
│  │   ✓     │   │    ✓✓    │   │    ✓✓     │   │    ✗     │     │
│  │ (gray)  │   │  (gray)  │   │  (blue)   │   │  (red)   │     │
│  └─────────┘   └──────────┘   └───────────┘   └──────────┘     │
│                                                                  │
│  Sent: Server received message                                  │
│  Delivered: Recipient's device received message                 │
│  Read: Recipient opened conversation                            │
│  Failed: Delivery failed after retries                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Flow:
  1. Sender sends message
  2. Server stores, responds with "sent" ack
  3. Server pushes to recipient
  4. Recipient sends "delivered" ack
  5. Server notifies sender of "delivered"
  6. Recipient opens chat, sends "read" ack
  7. Server notifies sender of "read"
```

### At-Least-Once Delivery

```
┌─────────────────────────────────────────────────────────────────┐
│                    DELIVERY GUARANTEE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Problem: Messages must never be lost                           │
│                                                                  │
│  Solution: At-least-once delivery + client deduplication        │
│                                                                  │
│  1. Client assigns unique client_message_id                     │
│                                                                  │
│  2. Server stores message with client_message_id                │
│     - If duplicate, return existing message_id                  │
│                                                                  │
│  3. Server attempts delivery                                    │
│     - If recipient offline, queue message                       │
│     - Retry on failure                                          │
│                                                                  │
│  4. Client acknowledges receipt                                 │
│     - Server marks as delivered                                 │
│                                                                  │
│  5. Client reconnects:                                          │
│     - Server sends all unacknowledged messages                  │
│     - Client deduplicates by client_message_id                  │
│                                                                  │
│  Deduplication on client:                                       │
│    messages_seen = set()                                        │
│    if message.client_msg_id in messages_seen:                   │
│        return  # Duplicate, ignore                              │
│    messages_seen.add(message.client_msg_id)                     │
│    display(message)                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Message Ordering

```
Problem: Messages must be ordered within a conversation

Solution: Sequence numbers per conversation

Messages table:
  conversation_id | sequence_num | message_id | content
  conv123         | 1            | msg001     | "Hello"
  conv123         | 2            | msg002     | "Hi there"
  conv123         | 3            | msg003     | "How are you?"

Client display:
  - Order by sequence_num
  - Gap detection: If receive seq 5 but have 3, request 4

Server assignment:
  - Use Redis INCR for conversation sequence
  - INCR conv:conv123:seq → returns next sequence number
  - Atomic operation ensures no gaps
```

---

## 7. Deep Dive: Group Messaging

### Group Message Fan-out

```
┌─────────────────────────────────────────────────────────────────┐
│                    GROUP MESSAGE FAN-OUT                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Group: 500 members                                             │
│  Sender: User A                                                 │
│                                                                  │
│  Approach 1: Fan-out on Write (small groups)                    │
│  ─────────────────────────────────────────                      │
│    1. Store original message once                               │
│    2. Create delivery record for each member                    │
│    3. Push to each online member                                │
│                                                                  │
│    Pros: Fast reads, simple                                     │
│    Cons: Write amplification for large groups                   │
│                                                                  │
│  Approach 2: Fan-out on Read (large groups)                     │
│  ─────────────────────────────────────────                      │
│    1. Store message once with group_id                          │
│    2. Members fetch group messages on connect                   │
│    3. Push notification for delivery                            │
│                                                                  │
│    Pros: Efficient writes                                       │
│    Cons: Slower reads, complex delivery tracking                │
│                                                                  │
│  Recommendation:                                                │
│    • Groups < 100: Fan-out on write                            │
│    • Groups > 100: Fan-out on read                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Group Storage Schema

```sql
CREATE TABLE groups (
    group_id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_by UUID NOT NULL,
    created_at TIMESTAMP NOT NULL,
    member_count INT DEFAULT 0,
    last_message_at TIMESTAMP
);

CREATE TABLE group_members (
    group_id UUID,
    user_id UUID,
    role VARCHAR(20) DEFAULT 'member',  -- admin, member
    joined_at TIMESTAMP NOT NULL,
    last_read_seq BIGINT DEFAULT 0,
    muted_until TIMESTAMP,
    PRIMARY KEY (group_id, user_id)
);

CREATE TABLE group_messages (
    group_id UUID,
    sequence_num BIGINT,
    message_id UUID NOT NULL,
    sender_id UUID NOT NULL,
    content TEXT,
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (group_id, sequence_num)
) WITH CLUSTERING ORDER BY (sequence_num DESC);

-- Index for user's group list
CREATE INDEX idx_group_members_user ON group_members(user_id);
```

---

## 8. Deep Dive: Presence System

### Online/Offline Status

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENCE SYSTEM                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Challenge: Track online status for 500M users                  │
│                                                                  │
│  Approach: Heartbeat-based presence                             │
│                                                                  │
│  1. Client sends heartbeat every 30 seconds                     │
│     POST /presence/heartbeat                                    │
│                                                                  │
│  2. Server updates Redis with TTL:                              │
│     SET user:123:online true EX 60                              │
│                                                                  │
│  3. Status query:                                               │
│     GET user:123:online                                         │
│     - Key exists → Online                                       │
│     - Key expired → Offline                                     │
│                                                                  │
│  4. Last seen for offline users:                                │
│     On disconnect: SET user:123:last_seen timestamp             │
│                                                                  │
│  Optimization for friends' status:                              │
│    - Subscribe to friends' presence channels                    │
│    - Push status changes, don't poll                            │
│                                                                  │
│  Privacy controls:                                              │
│    - User can hide online status                                │
│    - Only show to contacts                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Typing Indicator

```
Flow:
  1. User starts typing
  2. Client sends typing event (debounced)
  3. Server broadcasts to conversation participants
  4. Other clients show "typing..." for 3 seconds
  5. Auto-clear if no new typing event

Implementation:
  // Client side
  let typingTimeout;
  input.onKeyPress = () => {
    if (!typingTimeout) {
      socket.send({type: "typing", conversation_id: "conv123"});
    }
    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(() => {
      typingTimeout = null;
    }, 2000);  // Debounce 2 seconds
  };

  // Server broadcasts to other participants
  // Other clients clear indicator after 3 seconds if no new event
```

---

## 9. Database Design

### Message Storage (Cassandra)

```
Cassandra for messages:
  - Write-heavy workload
  - Time-series data (messages by time)
  - Easy horizontal scaling

CREATE TABLE messages (
    conversation_id text,
    message_id timeuuid,
    sender_id text,
    content text,
    media_url text,
    created_at timestamp,
    PRIMARY KEY ((conversation_id), message_id)
) WITH CLUSTERING ORDER BY (message_id DESC);

-- Efficient queries:
-- Get recent messages for conversation (paginated)
SELECT * FROM messages
WHERE conversation_id = 'conv123'
LIMIT 50;

-- Get messages before a certain point (infinite scroll)
SELECT * FROM messages
WHERE conversation_id = 'conv123'
AND message_id < some_message_id
LIMIT 50;
```

### User Conversations (Redis + PostgreSQL)

```
Redis for active data:
  # User's conversation list (sorted by last message)
  ZADD user:123:conversations timestamp conversation_id

  # Unread counts
  HINCRBY user:123:unread conv456 1

  # Get conversations with unread counts
  ZREVRANGE user:123:conversations 0 20 WITHSCORES

PostgreSQL for conversation metadata:
  CREATE TABLE conversations (
      conversation_id UUID PRIMARY KEY,
      type VARCHAR(10) NOT NULL,  -- direct, group
      created_at TIMESTAMP NOT NULL
  );

  CREATE TABLE conversation_participants (
      conversation_id UUID,
      user_id UUID,
      joined_at TIMESTAMP NOT NULL,
      PRIMARY KEY (conversation_id, user_id)
  );
```

---

## 10. Key Trade-offs

```
Trade-off 1: Message Storage Duration
  Chose: 30 days hot, then archive to cold
  Because: Balance cost and access patterns
  Impact: Older messages have higher latency

Trade-off 2: Delivery Guarantee
  Chose: At-least-once with client deduplication
  Over: Exactly-once (complex)
  Because: Simpler, reliable, handles edge cases

Trade-off 3: Presence Accuracy
  Chose: 60-second heartbeat TTL
  Because: Balance accuracy vs load
  Impact: Up to 60s delay in offline detection

Trade-off 4: Group Fan-out
  Chose: Hybrid based on group size
  Because: Optimize for common cases
  Complexity: Two code paths to maintain
```

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    WHATSAPP ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Real-time Layer:                                               │
│    • WebSocket Gateways (150M concurrent connections)           │
│    • Redis Pub/Sub for message routing                          │
│    • Session store for connection mapping                       │
│                                                                  │
│  Message Layer:                                                 │
│    • Kafka for message queue                                    │
│    • Cassandra for message storage                              │
│    • Sequence numbers for ordering                              │
│                                                                  │
│  Presence Layer:                                                │
│    • Redis with TTL for online status                           │
│    • Heartbeat-based presence                                   │
│    • Push-based status updates                                  │
│                                                                  │
│  Key Design Decisions:                                          │
│    • Distributed WebSocket with Redis coordination              │
│    • At-least-once delivery with deduplication                  │
│    • Hybrid fan-out for groups                                  │
│    • Eventually consistent presence                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interview Tips

```
Key points to hit:
  1. WebSocket connection management at scale
  2. Message delivery guarantees (at-least-once)
  3. Message ordering with sequence numbers
  4. Presence system design
  5. Group message fan-out strategy

Common follow-ups:
  - How to implement end-to-end encryption?
  - How to handle message search?
  - How to sync messages across devices?
  - How to implement voice/video calls?
```
