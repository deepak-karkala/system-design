# Twitter / News Feed

Design a social media feed system like Twitter's home timeline.

---

## 1. Requirements

### Functional Requirements
```
Core Features:
  1. Post tweets (text, images, videos)
  2. Follow/unfollow users
  3. View home timeline (feed of followed users' tweets)
  4. View user timeline (specific user's tweets)

Out of Scope:
  - Direct messages
  - Search
  - Trending topics
  - Ads
```

### Non-Functional Requirements
```
Scale:
  - 300M DAU
  - 500M total users
  - Average user follows 200 people
  - 600M tweets per day

Performance:
  - Timeline load: < 500ms
  - Tweet post: < 1s

Availability:
  - 99.9% uptime

Consistency:
  - Eventual consistency acceptable for timeline
```

---

## 2. Estimation

### Traffic
```
Tweets:
  600M tweets/day ÷ 86,400 ≈ 7,000 tweets/second
  Peak: 21,000 tweets/second

Timeline reads:
  300M DAU × 10 timeline loads/day = 3B reads/day
  3B ÷ 86,400 ≈ 35,000 reads/second
  Peak: 100,000 reads/second

Read:Write ratio ≈ 5:1
```

### Storage
```
Tweet size:
  - Tweet ID: 8 bytes
  - User ID: 8 bytes
  - Text: 280 chars = 280 bytes
  - Timestamps: 16 bytes
  - Metadata: 50 bytes
  Total: ~360 bytes

Daily tweet storage:
  600M × 360 bytes ≈ 200 GB/day

5-year storage:
  200 GB × 365 × 5 = 365 TB

Media (20% have images):
  600M × 20% × 1 MB = 120 TB/day
  5 years: 220 PB (with compression, dedup)
```

### Fan-out
```
Average followers: 200
Tweet creates 200 timeline updates

Celebrities (1M+ followers):
  1 tweet = 1M+ updates
  This is the challenge!
```

---

## 3. API Design

```
POST /tweets
  Request: {
    "text": "Hello world!",
    "media_ids": ["media123"]
  }
  Response: {
    "tweet_id": "1234567890",
    "created_at": "2024-01-15T10:30:00Z"
  }

GET /timeline/home?cursor=xxx&limit=20
  Response: {
    "tweets": [
      {"tweet_id": "123", "user_id": "456", "text": "...", ...}
    ],
    "next_cursor": "yyy"
  }

GET /timeline/user/{user_id}?cursor=xxx&limit=20
  Response: {
    "tweets": [...],
    "next_cursor": "yyy"
  }

POST /users/{user_id}/follow
DELETE /users/{user_id}/follow
```

---

## 4. High-Level Design

```
                              ┌─────────────┐
                              │   Clients   │
                              └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │     CDN     │
                              │  (media)    │
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
               │  Tweet  │     │ Timeline │    │  User    │
               │ Service │     │ Service  │    │ Service  │
               └────┬────┘     └────┬─────┘    └────┬─────┘
                    │               │               │
                    │          ┌────▼────┐          │
                    │          │ Timeline │          │
                    │          │  Cache   │          │
                    │          │ (Redis)  │          │
                    │          └────┬─────┘          │
                    │               │               │
                    └───────────────┼───────────────┘
                                    │
               ┌────────────────────┼────────────────────┐
               │                    │                    │
          ┌────▼────┐         ┌─────▼────┐         ┌─────▼────┐
          │ Tweet   │         │  Graph   │         │  Fan-out │
          │   DB    │         │   DB     │         │  Queue   │
          └─────────┘         └──────────┘         └────┬─────┘
                                                        │
                                                   ┌────▼────┐
                                                   │ Fan-out │
                                                   │ Workers │
                                                   └─────────┘
```

---

## 5. Deep Dive: Timeline Generation

### The Fan-out Problem

```
Two approaches:

1. Fan-out on Write (Push):
   When user tweets → Push to all followers' timelines

   ┌──────┐  Tweet   ┌─────────────┐
   │ User │ ────────>│ Fan-out     │
   └──────┘          │ Workers     │
                     └──────┬──────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
         Follower A    Follower B    Follower C
         Timeline      Timeline      Timeline

   Pros: Fast reads
   Cons: Slow writes for celebrities, storage for inactive users

2. Fan-out on Read (Pull):
   When user loads timeline → Fetch from followed users

   ┌──────┐  Load    ┌─────────────┐
   │ User │ ────────>│ Timeline    │
   └──────┘          │ Service     │
                     └──────┬──────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
         Following A   Following B   Following C
         Get tweets    Get tweets    Get tweets

   Pros: Less storage, no celebrity problem
   Cons: Slow reads (many fetches)
```

### Hybrid Approach (Recommended)

```
┌─────────────────────────────────────────────────────────────────┐
│                    HYBRID FAN-OUT                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Regular Users (< 10K followers):                               │
│    → Fan-out on Write                                           │
│    → Push tweets to followers' timelines                        │
│                                                                  │
│  Celebrities (> 10K followers):                                 │
│    → Fan-out on Read                                            │
│    → Followers fetch celebrity tweets at read time              │
│                                                                  │
│  Timeline Generation:                                            │
│    1. Read pre-computed timeline (from push)                    │
│    2. Fetch tweets from followed celebrities (pull)             │
│    3. Merge and sort by timestamp                               │
│    4. Return top N                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

def get_timeline(user_id):
    # Get pre-computed timeline (regular users' tweets)
    precomputed = timeline_cache.get(user_id)

    # Get followed celebrities
    celebrities = user_service.get_followed_celebrities(user_id)

    # Fetch recent tweets from celebrities
    celebrity_tweets = []
    for celeb in celebrities:
        tweets = tweet_cache.get_recent(celeb.id, limit=100)
        celebrity_tweets.extend(tweets)

    # Merge and sort
    all_tweets = precomputed + celebrity_tweets
    all_tweets.sort(key=lambda t: t.created_at, reverse=True)

    return all_tweets[:20]
```

---

## 6. Database Design

### Tweet Storage (Cassandra)

```
Table: tweets
Partition Key: tweet_id

{
    "tweet_id": "1234567890",
    "user_id": "user123",
    "text": "Hello world!",
    "media_ids": ["media1", "media2"],
    "created_at": "2024-01-15T10:30:00Z",
    "reply_count": 100,
    "retweet_count": 50,
    "like_count": 500
}

Table: user_tweets (for user timeline)
Partition Key: user_id
Clustering Key: created_at DESC

Allows efficient query: Get user's recent tweets
```

### Timeline Cache (Redis)

```
Key: timeline:{user_id}
Value: List of tweet IDs (most recent first)

Structure:
  timeline:user123 = [tweet999, tweet998, tweet997, ...]

Operations:
  LPUSH timeline:user123 tweet1000  # Add new tweet
  LRANGE timeline:user123 0 19      # Get top 20
  LTRIM timeline:user123 0 799      # Keep only 800

Size:
  800 tweets × 8 bytes = 6.4 KB per user
  300M active users × 6.4 KB = 1.9 TB
```

### Social Graph (Graph DB or Redis)

```
Followers/Following relationship:

Option 1: Redis Sets
  following:user123 = {user456, user789, ...}
  followers:user456 = {user123, user321, ...}

Option 2: Cassandra
  Table: follows
  Partition Key: follower_id
  Clustering Key: followee_id

  Table: followers
  Partition Key: followee_id
  Clustering Key: follower_id

Both tables for efficient queries in both directions.
```

---

## 7. Fan-out Service

```
┌─────────────────────────────────────────────────────────────────┐
│                    FAN-OUT SERVICE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Tweet Service publishes to Kafka:                           │
│     Topic: new_tweets                                           │
│     Message: { user_id, tweet_id, timestamp }                   │
│                                                                  │
│  2. Fan-out Workers consume:                                    │
│     - Get tweet author's followers                              │
│     - Filter out celebrities (> 10K followers)                  │
│     - For each follower:                                        │
│       - LPUSH to their timeline in Redis                        │
│       - LTRIM to limit size                                     │
│                                                                  │
│  3. Parallel processing:                                        │
│     - Partition Kafka by user_id                                │
│     - Scale workers horizontally                                │
│     - Batch updates for efficiency                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

def fan_out_tweet(tweet):
    if tweet.author.follower_count > CELEBRITY_THRESHOLD:
        return  # Skip fan-out for celebrities

    followers = get_followers(tweet.author_id)

    for batch in chunks(followers, 1000):
        pipeline = redis.pipeline()
        for follower_id in batch:
            pipeline.lpush(f"timeline:{follower_id}", tweet.tweet_id)
            pipeline.ltrim(f"timeline:{follower_id}", 0, 799)
        pipeline.execute()
```

---

## 8. Key Trade-offs

```
Trade-off 1: Push vs Pull
  Chose: Hybrid (push for regular, pull for celebrities)
  Because: Balances write amplification and read latency

Trade-off 2: Timeline Storage
  Chose: Store tweet IDs only in Redis, fetch full tweets separately
  Because: Reduces memory, allows tweet updates

Trade-off 3: Consistency
  Chose: Eventual consistency
  Because: Timeline doesn't need real-time accuracy

Trade-off 4: Celebrity Threshold
  Chose: 10K followers
  Because: Balances fan-out cost vs read complexity
  Note: Tune based on actual traffic patterns
```

---

## 9. Handling Hot Spots

### Celebrity Tweet Goes Viral

```
Problem: Celebrity tweets can spike read traffic

Solutions:
  1. Cache celebrity tweets aggressively
     - TTL: 1 hour
     - Replicate across cache nodes

  2. Pre-compute celebrity timelines
     - Maintain list of celebrities
     - Cache their recent tweets

  3. Rate limiting on timeline refreshes
     - Max 1 refresh per second per user
```

### Breaking News Events

```
Problem: Many users tweeting about same event

Solutions:
  1. Increase fan-out worker capacity (auto-scale)
  2. Prioritize timeline updates (queue with priority)
  3. Batch updates more aggressively during peaks
```

---

## 10. Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                   TWITTER ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Components:                                                     │
│    • Tweet Service: CRUD for tweets                             │
│    • Timeline Service: Generate/serve timelines                 │
│    • User Service: Profiles, follow graph                       │
│    • Fan-out Service: Push tweets to timelines                  │
│    • Media Service: Image/video storage (S3 + CDN)              │
│                                                                  │
│  Data Stores:                                                   │
│    • Cassandra: Tweets, user timelines                          │
│    • Redis: Timeline cache, follow graph cache                  │
│    • S3 + CDN: Media storage and delivery                       │
│    • Kafka: Event streaming for fan-out                         │
│                                                                  │
│  Key Design Decisions:                                          │
│    • Hybrid fan-out (push for most, pull for celebrities)       │
│    • Store tweet IDs in cache, fetch full tweets on demand      │
│    • Eventual consistency for timelines                         │
│    • Celebrity threshold at 10K followers                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interview Tips

```
Key points to hit:
  1. Fan-out on write vs read - this is THE key decision
  2. Explain the celebrity problem clearly
  3. Hybrid approach with clear threshold
  4. Timeline cache structure (IDs only)
  5. Eventual consistency is acceptable

Common follow-ups:
  - How to handle a user unfollowing?
  - How to rank timeline (not just chronological)?
  - How to handle deleted tweets?
  - How to add real-time updates (WebSocket)?
```
