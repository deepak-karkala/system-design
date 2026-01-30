# Estimation Examples

Worked examples for common system design estimation scenarios.

---

## Example 1: Twitter-like Social Platform

### Requirements
- 500 million registered users
- 200 million DAU (Daily Active Users)
- Each user views 100 tweets/day, posts 2 tweets/day
- 20% of tweets contain media (average 1 MB)
- Data retention: 10 years

### Traffic Estimation
```
Read Operations:
- Tweet views: 200M users × 100 tweets = 20 billion reads/day
- Average QPS: 20B ÷ 86,400 ≈ 230,000 reads/second
- Peak QPS: 230K × 3 = 700,000 reads/second

Write Operations:
- New tweets: 200M users × 2 tweets = 400 million writes/day
- Average QPS: 400M ÷ 86,400 ≈ 4,600 writes/second
- Peak QPS: 4.6K × 3 = 14,000 writes/second

Read:Write Ratio = 230K : 4.6K ≈ 50:1 (read-heavy)
```

### Storage Estimation
```
Tweet Data:
- Daily tweets: 400 million
- Tweet size: ~500 bytes (text + metadata)
- Daily text storage: 400M × 500B = 200 GB/day

Media Storage:
- Tweets with media: 400M × 20% = 80 million media/day
- Media size: 1 MB average
- Daily media storage: 80M × 1 MB = 80 TB/day

Total Daily Storage:
- 200 GB (text) + 80 TB (media) ≈ 80 TB/day

10-Year Storage:
- 80 TB × 365 × 10 = 292 PB
- With 3x replication: ~900 PB

Timeline Cache:
- Active users: 200M
- Timeline size: 100 tweets × 500 bytes = 50 KB/user
- Hot cache (20% of active): 40M × 50 KB = 2 TB
```

### Bandwidth Estimation
```
Reads:
- 20B tweet views × 500 bytes = 10 TB/day text
- Assume 10% have media viewed: 2B × 1 MB = 2 PB/day media
- Total egress: ~2 PB/day ≈ 185 Gbps average, 555 Gbps peak

Writes:
- 400M tweets × 500 bytes = 200 GB/day text
- 80M media × 1 MB = 80 TB/day media
- Total ingress: ~80 TB/day ≈ 7.4 Gbps
```

### Summary
```
Metric              | Value
--------------------|------------------
Read QPS (peak)     | 700,000
Write QPS (peak)    | 14,000
Daily storage       | 80 TB
10-year storage     | ~900 PB (with replication)
Peak bandwidth      | 555 Gbps (egress)
Cache size          | 2 TB (hot data)
```

---

## Example 2: YouTube-like Video Platform

### Requirements
- 1 billion registered users
- 100 million DAU
- Each user watches 5 videos/day (average 10 minutes)
- 1 million videos uploaded/day
- Average video size: 500 MB (after compression, multiple qualities)

### Traffic Estimation
```
Video Views:
- 100M users × 5 videos = 500 million video views/day
- Average: 500M ÷ 86,400 ≈ 5,800 views/second
- Peak: 5.8K × 3 = 17,400 views/second

Video Uploads:
- 1 million uploads/day
- Average: 1M ÷ 86,400 ≈ 12 uploads/second
- Peak: 12 × 5 = 60 uploads/second

Read:Write Ratio = 5,800 : 12 ≈ 500:1 (extremely read-heavy)
```

### Storage Estimation
```
Daily Video Storage:
- 1M videos × 500 MB = 500 TB/day

Annual Storage:
- 500 TB × 365 = 182.5 PB/year

5-Year Storage:
- 182.5 PB × 5 = ~900 PB
- With 3x replication: 2.7 EB (exabytes)

Metadata Storage:
- 1M videos × 10 KB metadata = 10 GB/day
- 5 years: ~18 TB (negligible compared to video)

Thumbnail Storage:
- 1M videos × 5 thumbnails × 50 KB = 250 GB/day
- 5 years: ~450 TB
```

### Bandwidth Estimation
```
Video Streaming (Egress):
- 500M views × 10 min × 5 Mbps bitrate
- = 500M × 600s × 5 Mbps = 1.5 × 10^18 bits/day
- = 187.5 PB/day
- Average: 187.5 PB ÷ 86,400s ≈ 17.4 Tbps
- Peak: 52 Tbps

Video Uploads (Ingress):
- 1M videos × 500 MB = 500 TB/day
- Average: 500 TB ÷ 86,400s ≈ 46 Gbps
```

### CDN Consideration
```
Without CDN: 17.4 Tbps from origin servers
With CDN (90% cache hit): 1.74 Tbps from origin

CDN cost consideration:
- Egress: 187.5 PB/day × $0.02/GB = $3.75M/day = $1.37B/year
- This is why CDN efficiency is critical
```

### Summary
```
Metric              | Value
--------------------|------------------
Video views/sec     | 17,400 (peak)
Uploads/sec         | 60 (peak)
Daily storage       | 500 TB
5-year storage      | 2.7 EB (with replication)
Peak egress         | 52 Tbps
Origin (with CDN)   | 5.2 Tbps
```

---

## Example 3: WhatsApp-like Messaging

### Requirements
- 2 billion registered users
- 500 million DAU
- 50 messages sent per user per day
- Average message size: 100 bytes
- 10% messages contain media (1 MB average)
- Message retention: forever (for users)

### Traffic Estimation
```
Messages:
- 500M users × 50 messages = 25 billion messages/day
- Average: 25B ÷ 86,400 ≈ 290,000 messages/second
- Peak: 290K × 5 = 1.45 million messages/second

Note: Each message involves:
- 1 write (store message)
- 1 read (recipient fetches)
- Push notification
```

### Storage Estimation
```
Text Messages:
- 25B messages × 100 bytes = 2.5 TB/day

Media Messages:
- 25B × 10% = 2.5B media/day
- 2.5B × 1 MB = 2.5 PB/day

Total Daily Storage:
- ~2.5 PB/day

Annual Storage:
- 2.5 PB × 365 = ~900 PB/year
- 3x replication: 2.7 EB/year

Message Indexes:
- User → Messages mapping
- ~50 bytes per message index
- 25B × 50 bytes = 1.25 TB/day
```

### Bandwidth Estimation
```
Ingress (sending messages):
- Text: 2.5 TB/day
- Media: 2.5 PB/day
- Total: ~2.5 PB/day ≈ 232 Gbps

Egress (receiving messages):
- Similar to ingress: ~232 Gbps
- Push notifications overhead: +10%
- Total: ~255 Gbps average, 765 Gbps peak
```

### Connection Estimation
```
Concurrent connections:
- 500M DAU
- Average online: 20% = 100M concurrent
- Peak: 200M concurrent

Each connection:
- WebSocket or long-polling
- Keep-alive: ~1 KB/minute overhead
- 100M × 1 KB/min = 100 GB/min = 1.67 GB/sec overhead
```

### Summary
```
Metric                | Value
----------------------|------------------
Messages/sec (peak)   | 1.45 million
Daily storage         | 2.5 PB
Annual storage        | 2.7 EB (replicated)
Peak bandwidth        | 765 Gbps
Concurrent connections| 200M (peak)
```

---

## Example 4: Uber-like Ride Sharing

### Requirements
- 50 million riders, 2 million drivers
- 10 million rides/day
- Driver location update every 4 seconds
- Trip data retention: 7 years

### Traffic Estimation
```
Ride Requests:
- 10M rides/day
- Average: 10M ÷ 86,400 ≈ 116 ride requests/second
- Peak (rush hour, 10x): 1,160 requests/second

Location Updates:
- Active drivers: 1 million (50% of 2M)
- Updates per driver: 86,400 ÷ 4 = 21,600/day
- Total updates: 1M × 21,600 = 21.6B updates/day
- Average: 21.6B ÷ 86,400 = 250,000 updates/second
- Peak: 500,000 updates/second

Driver Matching Queries:
- Each ride request triggers nearby driver search
- ~5 queries per match (retries, updates)
- 116 × 5 = 580 geo queries/second
- Peak: 5,800 geo queries/second
```

### Storage Estimation
```
Trip Data:
- 10M trips × 2 KB (route, fare, metadata) = 20 GB/day
- 7 years: 20 GB × 365 × 7 = 51 TB

Location History:
- 21.6B updates × 50 bytes = 1 TB/day
- Keep 30 days: 30 TB
- Archive compressed: ~10 TB

Geospatial Index:
- 2M drivers × location data
- Quadtree/Geohash: ~500 MB in memory
```

### Bandwidth Estimation
```
Location Updates:
- 21.6B updates × 50 bytes = 1 TB/day ingress

App Data (ride info, maps):
- 10M rides × 500 KB (map tiles, route) = 5 TB/day

Total:
- ~6 TB/day ≈ 555 Mbps average
- Peak: 1.7 Gbps
```

### Real-time Requirements
```
Latency Requirements:
- Driver location update: < 1 second end-to-end
- Ride matching: < 5 seconds
- ETA calculation: < 2 seconds

This drives:
- In-memory geospatial index
- Pub/sub for real-time updates
- Edge computing for low latency
```

### Summary
```
Metric                  | Value
------------------------|------------------
Ride requests/sec       | 1,160 (peak)
Location updates/sec    | 500,000 (peak)
Geo queries/sec         | 5,800 (peak)
Trip storage (7 years)  | 51 TB
Geospatial index        | 500 MB (in-memory)
Latency requirement     | < 1 second
```

---

## Estimation Cheat Sheet

### Quick Multipliers
```
1 Million/day = 12/second
10 Million/day = 116/second
100 Million/day = 1,160/second
1 Billion/day = 11,600/second
```

### Storage Quick Math
```
1 KB × 1 Million = 1 GB
1 KB × 1 Billion = 1 TB
1 MB × 1 Million = 1 TB
1 MB × 1 Billion = 1 PB
```

### Common Object Sizes
```
Object              | Size
--------------------|--------
Tweet/Short text    | 0.5-1 KB
User profile        | 1-10 KB
Thumbnail           | 10-50 KB
Photo (web)         | 200-500 KB
Photo (original)    | 2-5 MB
1-min video (SD)    | 10-20 MB
1-min video (HD)    | 50-100 MB
```

---

## Next Steps

Use these examples as templates for your specific system:
1. Identify similar patterns in your design
2. Adjust numbers based on your requirements
3. Focus on the dominant factors (usually storage or bandwidth)
4. Proceed to [API Design](../03-api-design/) or [Data Model](../04-data-model/)
