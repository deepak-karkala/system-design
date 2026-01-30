# Instagram / Photo Sharing

Design a photo sharing social network like Instagram.

---

## 1. Requirements

### Functional Requirements
```
Core Features:
  1. Upload photos/videos with captions
  2. Follow/unfollow users
  3. View home feed (posts from followed users)
  4. Like and comment on posts
  5. View user profiles

Out of Scope:
  - Stories (ephemeral content)
  - Direct messaging
  - Reels/short videos
  - Explore/discovery
```

### Non-Functional Requirements
```
Scale:
  - 1B monthly active users
  - 500M DAU
  - 100M photos uploaded per day
  - Average user follows 200 people

Performance:
  - Feed load: < 500ms
  - Photo upload: < 5 seconds
  - High-quality image display

Availability:
  - 99.99% uptime

Consistency:
  - Eventual for feed
  - Strong for likes/follows counts (eventually)
```

---

## 2. Estimation

### Traffic
```
Photo uploads:
  100M photos/day ÷ 86,400 ≈ 1,150 uploads/second
  Peak (2x): 2,300 uploads/second

Feed reads:
  500M DAU × 20 feed views/day = 10B reads/day
  10B ÷ 86,400 ≈ 115,000 reads/second
  Peak: 300,000 reads/second

Read:Write ratio ≈ 100:1 (very read-heavy)
```

### Storage
```
Photo storage:
  Average photo: 2 MB (multiple resolutions stored)
  100M photos × 2 MB = 200 TB/day
  5 years: 365 PB

Metadata:
  Per photo: ~1 KB
  100M × 1 KB = 100 GB/day
  5 years: 180 TB
```

### Bandwidth
```
Photo ingress:
  1,150 uploads/sec × 2 MB = 2.3 GB/second

Photo egress (CDN handles most):
  115,000 reads/sec × 500 KB avg = 57.5 GB/second
  95% served by CDN → Origin: 2.9 GB/second
```

---

## 3. API Design

```
Photo Upload:

POST /posts
  Headers: {
    "Content-Type": "multipart/form-data"
  }
  Body: {
    "media": [file],
    "caption": "Sunset at the beach #vacation",
    "location": {"lat": 37.7749, "lng": -122.4194, "name": "San Francisco"}
  }
  Response: {
    "post_id": "post123",
    "media_urls": {
      "thumbnail": "https://cdn.instagram.com/.../thumb.jpg",
      "standard": "https://cdn.instagram.com/.../standard.jpg",
      "full": "https://cdn.instagram.com/.../full.jpg"
    },
    "created_at": "2024-01-15T10:30:00Z"
  }

Feed:

GET /feed?cursor=xxx&limit=20
  Response: {
    "posts": [
      {
        "post_id": "post123",
        "user": {"id": "user456", "username": "johndoe", "avatar_url": "..."},
        "media_urls": {...},
        "caption": "...",
        "like_count": 1500,
        "comment_count": 42,
        "created_at": "2024-01-15T10:30:00Z",
        "is_liked": false
      }
    ],
    "next_cursor": "yyy"
  }

Interactions:

POST /posts/{post_id}/like
DELETE /posts/{post_id}/like

POST /posts/{post_id}/comments
  Request: {"text": "Great photo!"}

GET /posts/{post_id}/comments?cursor=xxx&limit=20

Social:

POST /users/{user_id}/follow
DELETE /users/{user_id}/follow

GET /users/{user_id}/profile
GET /users/{user_id}/posts?cursor=xxx&limit=20
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
                              │     CDN     │
                              │  (Images)   │
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
              │   Post    │   │   Feed     │   │   User    │
              │  Service  │   │  Service   │   │  Service  │
              └─────┬─────┘   └──────┬─────┘   └─────┬─────┘
                    │                │               │
                    │          ┌─────▼─────┐        │
                    │          │   Feed    │        │
                    │          │   Cache   │        │
                    │          │  (Redis)  │        │
                    │          └───────────┘        │
                    │                               │
         ┌──────────┴──────────┬───────────────────┘
         │                     │
    ┌────▼────┐          ┌─────▼────┐
    │  Image  │          │  Graph   │
    │ Storage │          │   DB     │
    │  (S3)   │          │ (follows)│
    └─────────┘          └──────────┘
         │
    ┌────▼────┐
    │  Image  │
    │Processing│
    │ Pipeline │
    └─────────┘
```

---

## 5. Deep Dive: Image Upload Pipeline

### Upload Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    IMAGE UPLOAD PIPELINE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Client uploads image                                        │
│     │ (Direct to S3 with pre-signed URL)                       │
│     ▼                                                           │
│  2. Upload to temporary S3 bucket                               │
│     │                                                           │
│     ▼                                                           │
│  3. S3 triggers Lambda/Processing Queue                         │
│     │                                                           │
│     ├──► Validate image (format, size, content moderation)      │
│     │                                                           │
│     ├──► Generate multiple resolutions:                         │
│     │    • Thumbnail: 150×150                                   │
│     │    • Small: 320×320                                       │
│     │    • Medium: 640×640                                      │
│     │    • Large: 1080×1080                                     │
│     │                                                           │
│     ├──► Optimize (compression, format conversion)              │
│     │    • Convert to WebP for modern browsers                  │
│     │    • Keep JPEG fallback                                   │
│     │                                                           │
│     ├──► Extract metadata (EXIF, location, dimensions)          │
│     │                                                           │
│     └──► Move to permanent storage                              │
│          │                                                       │
│          ▼                                                       │
│  4. Update post record with image URLs                          │
│     │                                                           │
│     ▼                                                           │
│  5. Push to CDN for global distribution                         │
│     │                                                           │
│     ▼                                                           │
│  6. Trigger feed fan-out                                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Image Storage Structure

```
S3 bucket structure:

instagram-photos/
├── originals/
│   └── 2024/01/15/
│       └── {post_id}/
│           └── original.jpg
├── processed/
│   └── 2024/01/15/
│       └── {post_id}/
│           ├── thumb_150.webp
│           ├── thumb_150.jpg
│           ├── small_320.webp
│           ├── small_320.jpg
│           ├── medium_640.webp
│           ├── medium_640.jpg
│           ├── large_1080.webp
│           └── large_1080.jpg

CDN URL pattern:
  https://cdn.instagram.com/{post_id}/{size}.{format}

Responsive images in client:
  <picture>
    <source srcset="...large.webp" type="image/webp" media="(min-width: 640px)">
    <source srcset="...medium.webp" type="image/webp">
    <img src="...medium.jpg" alt="...">
  </picture>
```

---

## 6. Deep Dive: News Feed Generation

### Feed Strategy (Hybrid Push/Pull)

```
┌─────────────────────────────────────────────────────────────────┐
│                    FEED GENERATION STRATEGY                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Same as Twitter: Hybrid approach based on follower count       │
│                                                                  │
│  Regular Users (< 10K followers):                               │
│  ─────────────────────────────────                              │
│    Fan-out on write:                                            │
│    1. User posts photo                                          │
│    2. Get list of followers                                     │
│    3. Add post_id to each follower's feed cache                 │
│                                                                  │
│  Celebrities (> 10K followers):                                 │
│  ───────────────────────────────                                │
│    Fan-out on read:                                             │
│    1. Post stored with celebrity flag                           │
│    2. When follower loads feed:                                 │
│       - Get precomputed feed (regular posts)                    │
│       - Fetch recent posts from followed celebrities            │
│       - Merge and rank                                          │
│                                                                  │
│  Feed Cache (Redis):                                            │
│  ───────────────────                                            │
│    Key: feed:{user_id}                                          │
│    Value: Sorted set of post_ids by timestamp                   │
│    ZADD feed:user123 timestamp post456                          │
│    ZREVRANGE feed:user123 0 19 → Top 20 posts                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Feed Ranking

```
Instagram doesn't show chronological feed anymore.
Ranking factors:

1. Interest Score:
   - User's past interactions with this author
   - Content type preferences (photos vs videos)
   - Hashtag interests

2. Recency:
   - Newer posts ranked higher
   - Decay function based on age

3. Relationship:
   - Close friends ranked higher
   - Frequent interactions boost ranking

4. Engagement:
   - Like/comment velocity
   - Save rate

Simple ranking formula:
  score = (interest × 0.4) + (recency × 0.3) + (relationship × 0.2) + (engagement × 0.1)

Implementation:
  - Pre-compute scores periodically
  - Store in feed cache with score
  - Real-time adjustments for new data
```

### Feed Assembly

```python
def get_feed(user_id, cursor=None, limit=20):
    # Get precomputed feed from cache
    feed_posts = redis.zrevrange(
        f"feed:{user_id}",
        start=cursor or 0,
        end=(cursor or 0) + limit - 1,
        withscores=True
    )

    # Get followed celebrities
    celebrities = get_followed_celebrities(user_id)

    # Fetch recent celebrity posts
    celebrity_posts = []
    for celeb_id in celebrities:
        posts = get_recent_posts(celeb_id, limit=10)
        celebrity_posts.extend(posts)

    # Merge and rank
    all_posts = merge_and_rank(feed_posts, celebrity_posts, user_id)

    # Fetch full post details
    post_ids = [p.id for p in all_posts[:limit]]
    posts = batch_get_posts(post_ids)

    # Add like/save status for current user
    posts = enrich_with_user_status(posts, user_id)

    return posts
```

---

## 7. Deep Dive: Likes and Comments

### Like System (High Write Volume)

```
Challenge: Millions of likes per second

Solution: Buffered writes with eventual consistency

┌─────────────────────────────────────────────────────────────────┐
│                    LIKE SYSTEM                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. User likes post                                             │
│     │                                                           │
│     ▼                                                           │
│  2. Write to Redis (immediate)                                  │
│     SADD post:{post_id}:likes {user_id}                        │
│     INCR post:{post_id}:like_count                             │
│     │                                                           │
│     ▼                                                           │
│  3. Queue async write to database                               │
│     │                                                           │
│     ▼                                                           │
│  4. Background worker persists to Cassandra                     │
│     │                                                           │
│     ▼                                                           │
│  5. Periodic sync: Redis count → Post metadata                  │
│                                                                  │
│  Consistency:                                                   │
│    - User sees their own like immediately (read-your-writes)   │
│    - Others see count update within seconds                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Like storage:
  Cassandra table:
    CREATE TABLE likes (
        post_id text,
        user_id text,
        created_at timestamp,
        PRIMARY KEY ((post_id), user_id)
    );

  Redis:
    post:{post_id}:likes → Set of user_ids (for "liked by you")
    post:{post_id}:like_count → Integer counter
```

### Comment System

```sql
Comments table (PostgreSQL):

CREATE TABLE comments (
    comment_id UUID PRIMARY KEY,
    post_id UUID NOT NULL,
    user_id UUID NOT NULL,
    parent_id UUID,  -- For replies
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    like_count INT DEFAULT 0
);

CREATE INDEX idx_comments_post ON comments(post_id, created_at DESC);
CREATE INDEX idx_comments_parent ON comments(parent_id) WHERE parent_id IS NOT NULL;

Comment display:
  - Top-level comments sorted by engagement/time
  - Replies nested under parent
  - Load more pattern for pagination
```

---

## 8. Database Design

### Post Metadata (PostgreSQL)

```sql
CREATE TABLE posts (
    post_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    caption TEXT,
    location_id UUID,
    created_at TIMESTAMP NOT NULL,

    -- Denormalized counters (updated async)
    like_count INT DEFAULT 0,
    comment_count INT DEFAULT 0,
    save_count INT DEFAULT 0,

    -- Content metadata
    media_type VARCHAR(10) NOT NULL,  -- image, video, carousel
    aspect_ratio FLOAT,

    -- Moderation
    is_hidden BOOLEAN DEFAULT false,
    sensitivity_score FLOAT DEFAULT 0
);

CREATE TABLE post_media (
    post_id UUID,
    media_index INT,  -- For carousels
    media_type VARCHAR(10) NOT NULL,
    storage_key TEXT NOT NULL,
    width INT,
    height INT,
    duration_seconds INT,  -- For videos
    PRIMARY KEY (post_id, media_index)
);

CREATE INDEX idx_posts_user ON posts(user_id, created_at DESC);
CREATE INDEX idx_posts_created ON posts(created_at DESC)
  WHERE is_hidden = false;
```

### Social Graph (Graph DB or Redis)

```
Following/Followers relationship:

Redis implementation:
  following:{user_id} → Set of followed user_ids
  followers:{user_id} → Set of follower user_ids

  SADD following:user123 user456
  SADD followers:user456 user123

  SMEMBERS following:user123 → All followed users
  SCARD followers:user456 → Follower count

For large accounts (millions of followers):
  - Paginate with SSCAN
  - Or use sorted set with join timestamp

Graph database (Neo4j) for advanced queries:
  - Mutual friends
  - Followers of followers
  - Shortest path between users
```

---

## 9. Key Trade-offs

```
Trade-off 1: Feed Ranking vs Chronological
  Chose: Algorithmic ranking
  Because: Better engagement, surfaces relevant content
  Impact: Users may miss posts from close friends
  Mitigation: "Close Friends" feature

Trade-off 2: Image Quality vs Storage Cost
  Chose: Multiple resolutions + WebP
  Because: Balance quality and bandwidth
  Trade-off: 4x storage per image

Trade-off 3: Like Count Consistency
  Chose: Eventually consistent (seconds delay)
  Because: Scale requirements
  Impact: Counts might be slightly off
  Acceptable: Non-critical data

Trade-off 4: Feed Precomputation
  Chose: Hybrid push/pull
  Because: Balance write amplification and read latency
  Complexity: Two code paths
```

---

## 10. Handling Edge Cases

### Viral Post

```
Problem: Post gets millions of likes/comments quickly

Solutions:
  1. Counter sharding:
     - Shard like counter across multiple Redis keys
     - INCR post:{post_id}:likes:{shard}
     - Sum shards for total (cached)

  2. Comment pagination:
     - Only load top comments initially
     - Load more on scroll
     - Cache top comments

  3. CDN pre-warming:
     - Detect viral posts early
     - Push to more edge locations
```

### User Deletes Post

```
Flow:
  1. Mark post as deleted (soft delete)
  2. Remove from all feed caches (async, best effort)
  3. Remove from CDN (purge request)
  4. Archive media to cold storage (legal retention)
  5. Delete likes/comments (GDPR compliance)

Implementation:
  - Publish "post_deleted" event to Kafka
  - Consumers handle cleanup in respective services
  - Idempotent operations for retry safety
```

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    INSTAGRAM ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Content Pipeline:                                              │
│    Client → S3 → Image Processing → CDN                         │
│                                                                  │
│  Feed Pipeline:                                                 │
│    Post → Kafka → Fan-out Workers → Redis Feed Cache            │
│                                                                  │
│  Data Stores:                                                   │
│    • PostgreSQL: Posts, users, comments                         │
│    • Redis: Feed cache, like counts, social graph               │
│    • Cassandra: Likes (write-heavy)                             │
│    • S3 + CDN: Images and videos                                │
│                                                                  │
│  Key Design Decisions:                                          │
│    • Multiple image resolutions for responsive display          │
│    • Hybrid fan-out (push for most, pull for celebrities)       │
│    • Eventually consistent counters                             │
│    • Algorithmic feed ranking                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interview Tips

```
Key points to hit:
  1. Image processing pipeline (resize, optimize, CDN)
  2. Feed generation (hybrid fan-out like Twitter)
  3. Handling high-volume writes (likes)
  4. Storage strategy for billions of images
  5. Feed ranking algorithm (not just chronological)

Common follow-ups:
  - How to implement Stories (ephemeral content)?
  - How to build the Explore page?
  - How to detect inappropriate content?
  - How to implement hashtag search?
```
