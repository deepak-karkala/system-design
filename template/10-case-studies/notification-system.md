# Notification System

Design a scalable notification system supporting push, SMS, and email.

---

## 1. Requirements

### Functional Requirements
```
Core Features:
  1. Send push notifications (iOS, Android, Web)
  2. Send SMS messages
  3. Send emails
  4. Support for templates and personalization
  5. User notification preferences
  6. Scheduling notifications

Out of Scope:
  - In-app notifications (separate system)
  - Rich media notifications (images, videos)
  - A/B testing notifications
```

### Non-Functional Requirements
```
Scale:
  - 1B notifications per day
  - 10M concurrent users
  - Support for large fan-outs (1M+ recipients)

Performance:
  - Push notification delivery: < 1 second (p95)
  - Email delivery: < 30 seconds (p95)
  - SMS delivery: < 10 seconds (p95)

Availability:
  - 99.99% uptime

Reliability:
  - At-least-once delivery
  - No duplicate notifications (best effort)
```

---

## 2. Estimation

### Traffic
```
Notifications:
  1B notifications/day ÷ 86,400 ≈ 11,500 notifications/second
  Peak (10x): 115,000 notifications/second

Breakdown by type:
  - Push: 70% = 8,000/second
  - Email: 25% = 2,900/second
  - SMS: 5% = 575/second
```

### Storage
```
Notification records:
  Per notification: 500 bytes (metadata, status)
  1B × 500 bytes = 500 GB/day

Keep 30 days of history: 15 TB

Templates:
  10,000 templates × 10 KB = 100 MB (negligible)

User preferences:
  100M users × 200 bytes = 20 GB
```

---

## 3. API Design

```
Send Notification:

POST /notifications/send
  Request: {
    "recipients": ["user123", "user456"],
    // OR for large fan-outs
    "audience": {
      "segment": "active_users",
      "filters": {"country": "US", "app_version_gte": "2.0"}
    },
    "channels": ["push", "email"],  // optional, defaults to user preference
    "template_id": "order_shipped",
    "data": {
      "order_id": "ORD123",
      "tracking_url": "https://..."
    },
    "priority": "high",  // high, normal, low
    "schedule_at": "2024-01-15T10:00:00Z"  // optional
  }
  Response: {
    "notification_id": "notif789",
    "status": "queued",
    "estimated_recipients": 2
  }

GET /notifications/{id}
  Response: {
    "notification_id": "notif789",
    "status": "sent",
    "stats": {
      "queued": 2,
      "sent": 2,
      "delivered": 2,
      "failed": 0,
      "opened": 1
    }
  }

User Preferences:

GET /users/{id}/notification-preferences
PUT /users/{id}/notification-preferences
  Request: {
    "push_enabled": true,
    "email_enabled": true,
    "sms_enabled": false,
    "quiet_hours": {"start": "22:00", "end": "08:00"},
    "categories": {
      "marketing": {"push": false, "email": true},
      "transactional": {"push": true, "email": true}
    }
  }

Templates:

POST /templates
GET /templates/{id}
PUT /templates/{id}
  Request: {
    "id": "order_shipped",
    "channels": {
      "push": {
        "title": "Order Shipped!",
        "body": "Your order {{order_id}} is on its way."
      },
      "email": {
        "subject": "Your order has shipped",
        "html_body": "<html>...</html>",
        "text_body": "..."
      }
    }
  }
```

---

## 4. High-Level Design

```
                              ┌─────────────┐
                              │   Clients   │
                              │(Internal    │
                              │ Services)   │
                              └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │  API        │
                              │  Gateway    │
                              └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │Notification │
                              │  Service    │
                              └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │   Message   │
                              │   Queue     │
                              │  (Kafka)    │
                              └──────┬──────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           │                         │                         │
     ┌─────▼─────┐            ┌──────▼─────┐            ┌─────▼─────┐
     │   Push    │            │   Email    │            │   SMS     │
     │  Worker   │            │   Worker   │            │  Worker   │
     └─────┬─────┘            └──────┬─────┘            └─────┬─────┘
           │                         │                         │
           │                         │                         │
     ┌─────▼─────┐            ┌──────▼─────┐            ┌─────▼─────┐
     │   APNs/   │            │ SendGrid/  │            │  Twilio/  │
     │   FCM     │            │ Mailgun    │            │  Nexmo    │
     └───────────┘            └────────────┘            └───────────┘
```

---

## 5. Deep Dive: Notification Processing Pipeline

### Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    NOTIFICATION PIPELINE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. API receives notification request                           │
│     │                                                           │
│     ▼                                                           │
│  2. Validate request                                            │
│     • Check rate limits                                         │
│     • Validate template exists                                  │
│     • Verify sender permissions                                 │
│     │                                                           │
│     ▼                                                           │
│  3. Resolve recipients (if audience query)                      │
│     • Query user segments                                       │
│     • Apply filters                                             │
│     • Chunk into batches of 1000                                │
│     │                                                           │
│     ▼                                                           │
│  4. For each recipient:                                         │
│     │                                                           │
│     ├── Check user preferences                                  │
│     │   • Is channel enabled?                                   │
│     │   • Is it quiet hours?                                    │
│     │   • Category preferences?                                 │
│     │                                                           │
│     ├── Check user devices/contacts                             │
│     │   • Get device tokens (push)                              │
│     │   • Get email address                                     │
│     │   • Get phone number (SMS)                                │
│     │                                                           │
│     ├── Render template with user data                          │
│     │                                                           │
│     └── Enqueue to channel-specific topic                       │
│         • Push: notifications.push                              │
│         • Email: notifications.email                            │
│         • SMS: notifications.sms                                │
│                                                                  │
│  5. Channel workers consume and send                            │
│     │                                                           │
│     ▼                                                           │
│  6. Track delivery status                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Message Format (Kafka)

```json
{
  "notification_id": "notif789",
  "user_id": "user123",
  "channel": "push",
  "priority": "high",
  "payload": {
    "device_tokens": ["token1", "token2"],
    "title": "Order Shipped!",
    "body": "Your order ORD123 is on its way.",
    "data": {
      "order_id": "ORD123",
      "action": "view_order"
    }
  },
  "created_at": "2024-01-15T10:00:00Z",
  "attempt": 1
}
```

---

## 6. Deep Dive: Push Notifications

### Push Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PUSH NOTIFICATION FLOW                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  iOS (APNs):                                                    │
│  ──────────                                                     │
│  Push Worker ──► APNs HTTP/2 ──► Apple Servers ──► iOS Device  │
│                                                                  │
│  Android (FCM):                                                 │
│  ─────────────                                                  │
│  Push Worker ──► FCM HTTP API ──► Google Servers ──► Android   │
│                                                                  │
│  Web (Web Push):                                                │
│  ───────────────                                                │
│  Push Worker ──► Web Push Protocol ──► Browser Push Service    │
│                                                                  │
│  Device Token Management:                                       │
│  ────────────────────────                                       │
│  • App registers with APNs/FCM on startup                       │
│  • Receives device token                                        │
│  • Sends token to our backend                                   │
│  • Backend stores token mapped to user                          │
│  • Token refreshed periodically                                 │
│                                                                  │
│  Device tokens table:                                           │
│    user_id | platform | token           | last_active           │
│    user123 | ios      | abc123...       | 2024-01-15            │
│    user123 | android  | xyz789...       | 2024-01-14            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Push Worker Implementation

```python
class PushWorker:
    def __init__(self):
        self.apns_client = APNsClient(credentials)
        self.fcm_client = FCMClient(credentials)

    def process_message(self, message):
        device_tokens = message['payload']['device_tokens']

        for token in device_tokens:
            try:
                if is_ios_token(token):
                    self.send_apns(token, message['payload'])
                else:
                    self.send_fcm(token, message['payload'])

                self.record_delivery(message['notification_id'], 'sent')

            except InvalidTokenError:
                # Token is invalid, remove from database
                self.remove_device_token(token)

            except RateLimitError:
                # Back off and retry
                raise RetryableError()

            except Exception as e:
                self.record_delivery(message['notification_id'], 'failed', str(e))

    def send_apns(self, token, payload):
        notification = {
            "aps": {
                "alert": {
                    "title": payload['title'],
                    "body": payload['body']
                },
                "sound": "default",
                "badge": 1
            },
            "custom_data": payload.get('data', {})
        }

        response = self.apns_client.send(
            token,
            notification,
            priority='high' if payload['priority'] == 'high' else 'normal'
        )

        if response.status_code != 200:
            raise APNsError(response)

    def send_fcm(self, token, payload):
        message = {
            "message": {
                "token": token,
                "notification": {
                    "title": payload['title'],
                    "body": payload['body']
                },
                "data": payload.get('data', {}),
                "android": {
                    "priority": "high" if payload['priority'] == 'high' else "normal"
                }
            }
        }

        response = self.fcm_client.send(message)
        return response
```

### Handling Token Invalidation

```
When to remove device tokens:
  1. APNs returns 410 (Unregistered)
  2. FCM returns "NotRegistered"
  3. User uninstalls app
  4. Token not used in 30 days

Process:
  1. Maintain last_active timestamp per token
  2. On invalid token response, delete immediately
  3. Nightly job: Delete tokens inactive > 30 days
```

---

## 7. Deep Dive: Email Delivery

### Email Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    EMAIL PIPELINE                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Email Worker receives message                               │
│     │                                                           │
│     ▼                                                           │
│  2. Render email template                                       │
│     • HTML and plain text versions                              │
│     • Inline CSS for compatibility                              │
│     • Personalize with user data                                │
│     │                                                           │
│     ▼                                                           │
│  3. Check suppression list                                      │
│     • Bounced addresses                                         │
│     • Unsubscribed users                                        │
│     • Spam complaints                                           │
│     │                                                           │
│     ▼                                                           │
│  4. Route to email provider                                     │
│     • Primary: SendGrid                                         │
│     • Fallback: Mailgun                                         │
│     │                                                           │
│     ▼                                                           │
│  5. Track delivery events (webhooks)                            │
│     • Delivered                                                 │
│     • Opened (tracking pixel)                                   │
│     • Clicked (link tracking)                                   │
│     • Bounced                                                   │
│     • Complained                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Email Deliverability

```
Maintaining sender reputation:

1. Authentication:
   • SPF: Authorize sending servers
   • DKIM: Sign emails cryptographically
   • DMARC: Policy for handling failures

2. List hygiene:
   • Remove bounced addresses immediately
   • Process unsubscribes within 24 hours
   • Sunset inactive recipients

3. Throttling:
   • Warm up new IPs gradually
   • Respect provider rate limits
   • Spread large sends over time

4. Content:
   • Avoid spam trigger words
   • Maintain text-to-image ratio
   • Include unsubscribe link

Monitoring:
  • Bounce rate < 2%
  • Complaint rate < 0.1%
  • Inbox placement rate > 95%
```

---

## 8. Deep Dive: Rate Limiting and Throttling

### Multi-Level Rate Limiting

```
┌─────────────────────────────────────────────────────────────────┐
│                    RATE LIMITING                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Level 1: API Rate Limits                                       │
│  ─────────────────────────                                      │
│    • Per client: 1000 requests/minute                           │
│    • Global: 10000 requests/minute                              │
│    • Sliding window counter in Redis                            │
│                                                                  │
│  Level 2: Per-User Rate Limits                                  │
│  ───────────────────────────                                    │
│    • Max 10 notifications/hour per user                         │
│    • Prevents notification spam to users                        │
│    • Queued if limit exceeded                                   │
│                                                                  │
│  Level 3: Provider Rate Limits                                  │
│  ────────────────────────────                                   │
│    • APNs: 4000 notifications/second per connection             │
│    • FCM: 600000 messages/minute                                │
│    • SendGrid: Based on plan                                    │
│    • Twilio: 1 SMS/second per number                            │
│                                                                  │
│  Implementation:                                                │
│    Use token bucket or leaky bucket per provider                │
│    If limit reached, back off exponentially                     │
│    Queue messages for later delivery                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Priority Queues

```
Kafka topics by priority:

notifications.push.high     → Process immediately
notifications.push.normal   → Standard processing
notifications.push.low      → Process when capacity available

Consumer configuration:
  - High priority: More workers, faster polling
  - Low priority: Fewer workers, batch processing

Use case examples:
  - High: OTP codes, security alerts, payment confirmations
  - Normal: Order updates, delivery status
  - Low: Marketing, recommendations
```

---

## 9. Database Design

### Notification Records (PostgreSQL + Cassandra)

```sql
-- PostgreSQL for recent/queryable notifications
CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY,
    sender_id UUID NOT NULL,
    template_id VARCHAR(100),
    audience JSONB,
    priority VARCHAR(10),
    scheduled_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL
);

CREATE TABLE notification_stats (
    notification_id UUID PRIMARY KEY,
    total_recipients INT DEFAULT 0,
    queued INT DEFAULT 0,
    sent INT DEFAULT 0,
    delivered INT DEFAULT 0,
    failed INT DEFAULT 0,
    opened INT DEFAULT 0,
    clicked INT DEFAULT 0
);

-- Cassandra for delivery logs (high volume)
CREATE TABLE delivery_log (
    notification_id uuid,
    user_id uuid,
    channel text,
    status text,
    timestamp timestamp,
    error_message text,
    PRIMARY KEY ((notification_id), user_id, channel)
);

-- User preferences (PostgreSQL)
CREATE TABLE user_notification_preferences (
    user_id UUID PRIMARY KEY,
    push_enabled BOOLEAN DEFAULT true,
    email_enabled BOOLEAN DEFAULT true,
    sms_enabled BOOLEAN DEFAULT false,
    quiet_hours JSONB,
    category_preferences JSONB
);

-- Device tokens (PostgreSQL)
CREATE TABLE device_tokens (
    user_id UUID,
    platform VARCHAR(20),
    token TEXT NOT NULL,
    app_version VARCHAR(20),
    last_active TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (user_id, token)
);

CREATE INDEX idx_tokens_last_active ON device_tokens(last_active);
```

### Template Storage

```sql
CREATE TABLE notification_templates (
    template_id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50),
    channels JSONB NOT NULL,  -- push, email, sms content
    variables TEXT[],  -- Required variables for validation
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    version INT DEFAULT 1
);

-- Example template content:
{
  "push": {
    "title": "Order {{status}}",
    "body": "Your order #{{order_id}} is now {{status}}."
  },
  "email": {
    "subject": "Order Update: {{status}}",
    "html_body": "<html>...</html>",
    "text_body": "Your order #{{order_id}}..."
  },
  "sms": {
    "body": "Order #{{order_id}} is {{status}}. Track: {{tracking_url}}"
  }
}
```

---

## 10. Key Trade-offs

```
Trade-off 1: Delivery Guarantee
  Chose: At-least-once delivery
  Because: Better to duplicate than miss
  Mitigation: Idempotency keys, client-side dedup

Trade-off 2: Multi-Provider vs Single Provider
  Chose: Multi-provider with fallback
  Because: Reliability, cost optimization
  Complexity: More integration work, routing logic

Trade-off 3: Sync vs Async
  Chose: Async with queue
  Because: Handle spikes, provide back-pressure
  Trade-off: Slightly delayed delivery

Trade-off 4: Per-User Rate Limits
  Chose: 10 notifications/hour per user
  Because: Prevent spam, improve experience
  Trade-off: May delay important notifications
  Mitigation: Exempt transactional from limits
```

---

## 11. Handling Edge Cases

### Large Fan-Out (1M+ recipients)

```
Problem: Marketing blast to all users

Solution: Chunked processing
  1. Split audience into chunks of 10,000
  2. Create sub-jobs for each chunk
  3. Process chunks in parallel
  4. Aggregate stats across chunks
  5. Implement circuit breaker if failure rate high

Throttling:
  - Send at 10% of max rate initially
  - Ramp up if no issues
  - Spread over hours if low priority
```

### Provider Outage

```
Detection:
  - Monitor error rates per provider
  - Health checks every 30 seconds
  - Circuit breaker trips at 50% error rate

Response:
  1. Failover to backup provider
  2. Queue messages if no backup
  3. Alert operations team
  4. Retry failed messages when recovered
```

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    NOTIFICATION SYSTEM ARCHITECTURE              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Ingestion:                                                     │
│    API Gateway → Notification Service → Kafka                   │
│                                                                  │
│  Processing:                                                    │
│    Kafka Topics (by channel & priority)                         │
│    → Push Workers → APNs/FCM                                    │
│    → Email Workers → SendGrid/Mailgun                           │
│    → SMS Workers → Twilio                                       │
│                                                                  │
│  Data Stores:                                                   │
│    • PostgreSQL: Notifications, templates, preferences          │
│    • Cassandra: Delivery logs (high volume)                     │
│    • Redis: Rate limiting, device token cache                   │
│                                                                  │
│  Key Design Decisions:                                          │
│    • Async processing via message queue                         │
│    • Multi-provider with failover                               │
│    • Priority queues for different urgency levels               │
│    • At-least-once delivery guarantee                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interview Tips

```
Key points to hit:
  1. Async architecture with message queue
  2. Multi-channel support (push, email, SMS)
  3. Rate limiting at multiple levels
  4. Provider failover strategy
  5. User preferences and suppression

Common follow-ups:
  - How to handle notification templates?
  - How to track notification analytics?
  - How to prevent notification fatigue?
  - How to handle time zones?
```
