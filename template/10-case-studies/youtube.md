# YouTube / Video Streaming

Design a video streaming platform like YouTube or Netflix.

---

## 1. Requirements

### Functional Requirements
```
Core Features:
  1. Upload videos
  2. Stream/watch videos
  3. Search videos
  4. Like/comment on videos
  5. Subscribe to channels

Out of Scope:
  - Live streaming
  - Recommendations (mention briefly)
  - Monetization/Ads
  - Video editing
```

### Non-Functional Requirements
```
Scale:
  - 2B monthly active users
  - 500M DAU
  - 500 hours of video uploaded per minute
  - 1B video views per day

Performance:
  - Video start time: < 2 seconds
  - Rebuffering: < 1% of watch time
  - Upload processing: < 30 minutes for 1-hour video

Availability:
  - 99.99% uptime

Consistency:
  - Eventual for view counts, likes
  - Strong for upload confirmation
```

---

## 2. Estimation

### Traffic
```
Video views:
  1B views/day ÷ 86,400 ≈ 11,500 views/second
  Peak: 50,000 views/second

Video uploads:
  500 hours/minute = 30,000 hours/day
  Average video length: 5 minutes
  30,000 × 60 / 5 = 360,000 videos/day
  ≈ 4 videos/second
```

### Storage
```
Video storage:
  Original upload: ~1GB per hour of video
  500 hours/minute × 60 × 24 = 720,000 hours/day
  720,000 × 1 GB = 720 TB/day of raw uploads

After encoding (multiple resolutions):
  360p: 0.5 GB/hour
  480p: 1 GB/hour
  720p: 2 GB/hour
  1080p: 4 GB/hour
  4K: 15 GB/hour
  Total: ~22 GB per hour of video
  720,000 × 22 GB = 15.8 PB/day

5 years: 15.8 PB × 365 × 5 = 28.8 EB (exabytes)
```

### Bandwidth
```
Streaming:
  Average bitrate: 5 Mbps (1080p)
  50,000 concurrent viewers at peak
  50,000 × 5 Mbps = 250 Gbps egress

With CDN: 95%+ served from edge
  Origin bandwidth: ~12.5 Gbps
```

---

## 3. API Design

```
Video Upload:

POST /videos/upload/initiate
  Request: {
    "title": "My Video",
    "description": "Description",
    "tags": ["tech", "tutorial"]
  }
  Response: {
    "upload_id": "upload123",
    "upload_url": "https://upload.youtube.com/...",
    "expires_at": "2024-01-15T11:00:00Z"
  }

PUT /videos/upload/{upload_id}/chunk
  Headers: {
    "Content-Range": "bytes 0-1048575/10485760"
  }
  Body: [binary chunk data]

POST /videos/upload/{upload_id}/complete
  Response: {
    "video_id": "vid456",
    "status": "processing"
  }

Video Streaming:

GET /videos/{video_id}/manifest
  Response: {
    "video_id": "vid456",
    "formats": [
      {"quality": "1080p", "url": "https://cdn.../vid456/1080p.m3u8"},
      {"quality": "720p", "url": "https://cdn.../vid456/720p.m3u8"},
      {"quality": "480p", "url": "https://cdn.../vid456/480p.m3u8"}
    ]
  }

GET /videos/{video_id}
  Response: {
    "video_id": "vid456",
    "title": "My Video",
    "channel": {"id": "ch123", "name": "TechChannel"},
    "views": 1500000,
    "likes": 50000,
    "duration": 600,
    "thumbnail_url": "https://cdn.../vid456/thumb.jpg"
  }

Search:

GET /search?q=tutorial&type=video&page_token=xxx
  Response: {
    "results": [...],
    "next_page_token": "yyy"
  }
```

---

## 4. High-Level Design

```
                              ┌─────────────┐
                              │   Clients   │
                              │(Web/Mobile) │
                              └──────┬──────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
              ┌─────▼─────┐    ┌─────▼─────┐   ┌─────▼─────┐
              │    CDN    │    │    API    │   │  Upload   │
              │ (Streaming)│    │  Gateway  │   │  Service  │
              └─────┬─────┘    └─────┬─────┘   └─────┬─────┘
                    │                │               │
                    │          ┌─────▼─────┐        │
                    │          │   Video   │        │
                    │          │  Service  │        │
                    │          └─────┬─────┘        │
                    │                │               │
         ┌──────────┴────┐     ┌─────▼─────┐   ┌───▼────┐
         │               │     │   User    │   │  Blob  │
    ┌────▼────┐    ┌─────▼───┐ │  Service  │   │ Storage│
    │ Origin  │    │ Search  │ └───────────┘   │  (S3)  │
    │ Storage │    │(Elastic)│                 └───┬────┘
    └─────────┘    └─────────┘                     │
                                              ┌────▼─────┐
                                              │ Encoding │
                                              │ Pipeline │
                                              └────┬─────┘
                                                   │
                                              ┌────▼─────┐
                                              │ Message  │
                                              │  Queue   │
                                              └──────────┘
```

---

## 5. Deep Dive: Video Upload & Processing

### Upload Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    VIDEO UPLOAD PIPELINE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Client initiates upload                                     │
│     │                                                           │
│     ▼                                                           │
│  2. Upload Service returns pre-signed URL                       │
│     │                                                           │
│     ▼                                                           │
│  3. Client uploads chunks directly to Blob Storage              │
│     │ (Parallel uploads, resumable)                             │
│     ▼                                                           │
│  4. Upload complete notification to Message Queue               │
│     │                                                           │
│     ▼                                                           │
│  5. Encoding Pipeline picks up job                              │
│     │                                                           │
│     ├──► Video Validation (format, length, content)             │
│     │                                                           │
│     ├──► Generate thumbnail                                     │
│     │                                                           │
│     ├──► Transcode to multiple resolutions                      │
│     │    • 360p, 480p, 720p, 1080p, 4K                         │
│     │    • Multiple codecs (H.264, VP9, AV1)                   │
│     │                                                           │
│     ├──► Generate adaptive streaming manifests                  │
│     │    • HLS (.m3u8)                                          │
│     │    • DASH (.mpd)                                          │
│     │                                                           │
│     └──► Update video status to "ready"                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Encoding Pipeline

```
Parallel encoding for speed:

┌─────────────┐
│ Original    │
│ Video       │
└──────┬──────┘
       │
       ├──────────────────────────────────────────┐
       │                                          │
       ▼                                          ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Split into   │  │ Split into   │  │ Split into   │
│ Segment 1    │  │ Segment 2    │  │ Segment 3    │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       ▼                 ▼                 ▼
   Encode to         Encode to         Encode to
   all formats       all formats       all formats
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │   Combine    │
                  │   Segments   │
                  └──────────────┘

Video encoding is CPU-intensive:
  - Use dedicated encoding workers
  - GPU acceleration (NVENC)
  - Distributed across multiple machines
```

### Storage Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    STORAGE TIERS                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Hot Storage (S3 Standard):                                     │
│    • Videos < 30 days old                                       │
│    • Popular videos (high view count)                           │
│    • Fast access, higher cost                                   │
│                                                                  │
│  Warm Storage (S3 Infrequent Access):                           │
│    • Videos 30-180 days old                                     │
│    • Medium access frequency                                    │
│    • Lower cost, retrieval fee                                  │
│                                                                  │
│  Cold Storage (S3 Glacier):                                     │
│    • Videos > 180 days old, rarely accessed                     │
│    • Archive tier                                               │
│    • Lowest cost, minutes to retrieve                           │
│                                                                  │
│  Intelligent tiering based on access patterns                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Deep Dive: Video Streaming

### Adaptive Bitrate Streaming (ABR)

```
┌─────────────────────────────────────────────────────────────────┐
│                    ADAPTIVE STREAMING                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  How it works:                                                  │
│                                                                  │
│  1. Video split into small segments (2-10 seconds each)         │
│  2. Each segment encoded at multiple bitrates                   │
│  3. Client requests manifest file (playlist)                    │
│  4. Client downloads segments based on bandwidth                │
│                                                                  │
│  Example HLS Manifest (.m3u8):                                  │
│                                                                  │
│  #EXTM3U                                                        │
│  #EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360          │
│  360p/playlist.m3u8                                             │
│  #EXT-X-STREAM-INF:BANDWIDTH=1400000,RESOLUTION=842x480         │
│  480p/playlist.m3u8                                             │
│  #EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1280x720        │
│  720p/playlist.m3u8                                             │
│  #EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080       │
│  1080p/playlist.m3u8                                            │
│                                                                  │
│  Bandwidth estimation:                                          │
│    Client measures download speed of each segment               │
│    Switches quality based on buffer level and throughput        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### CDN Architecture

```
                         ┌─────────────┐
                         │   Origin    │
                         │   Server    │
                         └──────┬──────┘
                                │
           ┌────────────────────┼────────────────────┐
           │                    │                    │
    ┌──────▼──────┐      ┌──────▼──────┐      ┌──────▼──────┐
    │  Regional   │      │  Regional   │      │  Regional   │
    │    PoP      │      │    PoP      │      │    PoP      │
    │  (US-East)  │      │  (Europe)   │      │  (Asia)     │
    └──────┬──────┘      └──────┬──────┘      └──────┬──────┘
           │                    │                    │
    ┌──────┴──────┐      ┌──────┴──────┐      ┌──────┴──────┐
    │             │      │             │      │             │
┌───▼───┐    ┌───▼───┐  ...           ...    ...
│ Edge  │    │ Edge  │
│  PoP  │    │  PoP  │
└───┬───┘    └───┬───┘
    │            │
 Users        Users

CDN Strategy:
  - Popular videos: Cached at edge (95%+ cache hit)
  - Less popular: Cached at regional PoPs
  - Long tail: Fetch from origin

Cache warming:
  - Pre-push popular content to edge
  - Predict trending videos
```

### Video Player Logic

```python
class AdaptivePlayer:
    def __init__(self):
        self.buffer_size = 0  # seconds of video buffered
        self.current_quality = "720p"
        self.bandwidth_history = []

    def estimate_bandwidth(self, segment_size, download_time):
        bandwidth = segment_size / download_time
        self.bandwidth_history.append(bandwidth)
        # Use weighted average of recent samples
        return self.weighted_average(self.bandwidth_history[-5:])

    def select_quality(self, available_qualities, estimated_bandwidth):
        # Buffer-based algorithm
        if self.buffer_size < 5:  # Low buffer, prioritize stability
            return self.get_lower_quality(self.current_quality)
        elif self.buffer_size > 30:  # High buffer, try higher quality
            for quality in sorted(available_qualities, reverse=True):
                if quality.bitrate < estimated_bandwidth * 0.8:
                    return quality
        return self.current_quality

    def handle_rebuffer(self):
        # Drop to lowest quality immediately
        self.current_quality = "360p"
        # Log for analytics
        self.report_rebuffer_event()
```

---

## 7. Database Design

### Video Metadata (PostgreSQL)

```sql
CREATE TABLE videos (
    video_id UUID PRIMARY KEY,
    channel_id UUID NOT NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    duration_seconds INT NOT NULL,
    status VARCHAR(20) NOT NULL,  -- processing, ready, failed
    visibility VARCHAR(20) DEFAULT 'public',
    upload_date TIMESTAMP NOT NULL,

    -- Denormalized for read performance
    view_count BIGINT DEFAULT 0,
    like_count INT DEFAULT 0,
    dislike_count INT DEFAULT 0,
    comment_count INT DEFAULT 0,

    CONSTRAINT valid_status CHECK (status IN ('processing', 'ready', 'failed'))
);

CREATE TABLE video_formats (
    video_id UUID REFERENCES videos(video_id),
    quality VARCHAR(10) NOT NULL,  -- 360p, 720p, 1080p
    codec VARCHAR(10) NOT NULL,    -- h264, vp9, av1
    bitrate INT NOT NULL,
    storage_url TEXT NOT NULL,
    manifest_url TEXT NOT NULL,
    PRIMARY KEY (video_id, quality, codec)
);

CREATE INDEX idx_videos_channel ON videos(channel_id, upload_date DESC);
CREATE INDEX idx_videos_popular ON videos(view_count DESC)
  WHERE status = 'ready' AND visibility = 'public';
```

### View Counts (Redis + Cassandra)

```
Challenge: Billions of view increments per day

Solution: Write-behind pattern

1. Redis for real-time counting:
   INCR video:vid123:views

2. Batch flush to Cassandra every minute:
   INSERT INTO video_views (video_id, date, hour, count)
   VALUES ('vid123', '2024-01-15', 14, 50000)

3. Aggregate daily totals:
   SELECT SUM(count) FROM video_views
   WHERE video_id = 'vid123' AND date = '2024-01-15'

Cassandra schema (time-series optimized):
  CREATE TABLE video_views (
      video_id text,
      date date,
      hour int,
      view_count counter,
      PRIMARY KEY ((video_id), date, hour)
  ) WITH CLUSTERING ORDER BY (date DESC, hour DESC);
```

---

## 8. Key Trade-offs

```
Trade-off 1: Encoding Depth
  Chose: Multiple resolutions + codecs
  Because: Better user experience across devices/bandwidth
  Cost: Higher storage and compute

Trade-off 2: CDN Cache Strategy
  Chose: Cache everything at edge for 24 hours
  Because: Simplicity, good hit rate for popular content
  Alternative: Intelligent caching based on popularity

Trade-off 3: View Count Accuracy
  Chose: Eventually consistent (few minutes delay)
  Because: Scale requirements make real-time impractical
  Impact: Users might see slightly stale counts

Trade-off 4: Storage Tiers
  Chose: Automatic tiering based on access
  Because: Balance cost and performance
  Complexity: Need monitoring for access patterns
```

---

## 9. Handling Edge Cases

### Video Goes Viral

```
Problem: Sudden spike in views for a single video

Solution:
  1. CDN auto-scaling
     - Edge nodes cache popular segments
     - Shield layer protects origin

  2. Pre-warming
     - Detect trending videos early
     - Push to more edge locations

  3. Origin protection
     - Rate limit origin requests
     - Queue non-critical requests
```

### Large File Upload Failure

```
Problem: Network drops during multi-GB upload

Solution: Resumable uploads
  1. Split file into chunks (5-10 MB each)
  2. Upload chunks independently
  3. Server tracks uploaded chunks
  4. Client resumes from last successful chunk

  POST /upload/status/{upload_id}
  Response: {
    "uploaded_chunks": [0, 1, 2, 5, 6],  // Missing 3, 4
    "total_chunks": 100
  }
```

---

## 10. Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    YOUTUBE ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Upload Path:                                                   │
│    Client → Upload Service → Blob Storage → Encoding Queue      │
│    → Encoding Workers → CDN Origin                              │
│                                                                  │
│  Streaming Path:                                                │
│    Client → CDN Edge → CDN Shield → Origin                      │
│                                                                  │
│  Data Stores:                                                   │
│    • PostgreSQL: Video metadata, channels                       │
│    • Redis: View counters, session cache                        │
│    • Cassandra: Time-series analytics                           │
│    • S3: Video files (hot/warm/cold tiers)                      │
│    • Elasticsearch: Video search                                │
│                                                                  │
│  Key Design Decisions:                                          │
│    • Chunked, resumable uploads                                 │
│    • Adaptive bitrate streaming (HLS/DASH)                      │
│    • Multi-tier CDN with edge caching                           │
│    • Eventually consistent view counts                          │
│    • Parallel video encoding                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interview Tips

```
Key points to hit:
  1. Video encoding pipeline (parallel, multiple formats)
  2. Adaptive bitrate streaming concept
  3. CDN architecture and caching strategy
  4. Storage tiering for cost optimization
  5. Handling view count at scale

Common follow-ups:
  - How to implement video recommendations?
  - How to handle live streaming?
  - How to detect and remove copyrighted content?
  - How to implement video comments at scale?
```
