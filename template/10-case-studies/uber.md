# Uber / Ride Sharing

Design a ride-sharing service like Uber or Lyft.

---

## 1. Requirements

### Functional Requirements
```
Rider Features:
  1. Request a ride (pickup, destination)
  2. See nearby available drivers
  3. Get matched with a driver
  4. Track driver location in real-time
  5. Complete ride and pay

Driver Features:
  1. Go online/offline
  2. Update location continuously
  3. Accept/decline ride requests
  4. Navigate to rider and destination
  5. Complete ride and receive payment

Out of Scope:
  - Surge pricing (mention briefly)
  - Driver ratings
  - Scheduled rides
  - Ride sharing (pool)
```

### Non-Functional Requirements
```
Scale:
  - 50M riders, 2M drivers
  - 10M rides per day
  - 1M concurrent drivers at peak

Performance:
  - Matching latency: < 5 seconds
  - Location update: Every 4 seconds
  - Real-time tracking: < 1 second delay

Availability:
  - 99.99% uptime (critical service)

Consistency:
  - Strong for ride state
  - Eventual for location updates
```

---

## 2. Estimation

### Traffic
```
Ride requests:
  10M rides/day ÷ 86,400 ≈ 116 rides/second
  Peak (rush hour, 10x): 1,160 rides/second

Location updates:
  1M active drivers × 1 update/4 seconds
  = 250,000 location updates/second
  Peak: 500,000 updates/second
```

### Storage
```
Location data:
  Per update: driver_id (8B) + lat/lng (16B) + timestamp (8B) = 32B
  500K updates/sec × 32B = 16 MB/second

Keep 30 days of location history:
  16 MB × 86,400 × 30 = 41 TB

Ride data:
  Per ride: ~2 KB (route, fare, metadata)
  10M rides × 2 KB = 20 GB/day
  1 year: 7.3 TB
```

### Geospatial
```
Geohash precision:
  - Precision 6: ~1.2 km × 0.6 km cells
  - Precision 7: ~150m × 150m cells

For driver matching:
  - Use precision 6 for initial search
  - Expand to neighboring cells if needed
```

---

## 3. API Design

```
Rider APIs:

POST /rides/request
  Request: {
    "pickup": {"lat": 37.7749, "lng": -122.4194},
    "destination": {"lat": 37.3382, "lng": -121.8863},
    "ride_type": "uberx"
  }
  Response: {
    "ride_id": "ride123",
    "status": "matching",
    "estimated_fare": 25.50
  }

GET /rides/{ride_id}
  Response: {
    "ride_id": "ride123",
    "status": "driver_arriving",
    "driver": {"id": "driver456", "name": "John", "car": "Toyota Camry"},
    "driver_location": {"lat": 37.7750, "lng": -122.4190},
    "eta_minutes": 3
  }

Driver APIs:

POST /drivers/location
  Request: {
    "lat": 37.7749,
    "lng": -122.4194,
    "heading": 180,
    "speed": 30
  }

POST /rides/{ride_id}/accept
POST /rides/{ride_id}/arrive
POST /rides/{ride_id}/start
POST /rides/{ride_id}/complete
```

---

## 4. High-Level Design

```
                              ┌─────────────┐
                              │   Clients   │
                              │(Rider/Driver│
                              │    Apps)    │
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
               │  Ride   │     │ Location │    │  User    │
               │ Service │     │ Service  │    │ Service  │
               └────┬────┘     └────┬─────┘    └──────────┘
                    │               │
                    │          ┌────▼────┐
                    │          │Geospatial│
                    │          │  Index   │
                    │          └────┬─────┘
                    │               │
               ┌────▼────┐    ┌─────▼────┐
               │ Matching│    │ Location │
               │ Service │    │   Store  │
               └────┬────┘    └──────────┘
                    │
               ┌────▼────┐
               │  Ride   │
               │   DB    │
               └─────────┘

Additional Components:
  - Notification Service (push notifications)
  - Payment Service
  - Analytics Service
```

---

## 5. Deep Dive: Location Service

### Location Updates (Write Path)

```
┌─────────────────────────────────────────────────────────────────┐
│                    LOCATION UPDATE FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Driver App                                                      │
│      │                                                           │
│      │ Every 4 seconds                                          │
│      ▼                                                           │
│  ┌─────────────┐                                                │
│  │  Location   │                                                │
│  │   Service   │                                                │
│  └──────┬──────┘                                                │
│         │                                                        │
│    ┌────┼────┐                                                  │
│    │    │    │                                                   │
│    ▼    ▼    ▼                                                   │
│  Redis  Kafka  Geospatial                                       │
│  (cache) (history) Index                                        │
│                                                                  │
│  Redis: driver:123 → {lat, lng, updated_at}                     │
│  Kafka: location_updates → Analytics                            │
│  Geospatial: geohash:9q8yy → [driver123, driver456, ...]       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Geospatial Indexing

```
Options:

1. Geohash + Redis:
   Key: geohash:9q8yyk
   Value: Set of driver IDs

   GEOADD drivers:locations -122.4194 37.7749 driver123
   GEORADIUS drivers:locations -122.4194 37.7749 5 km

2. QuadTree (In-memory):
   - Divide space recursively into quadrants
   - Efficient for nearby queries
   - Needs to be distributed

3. S2 Geometry (Google's approach):
   - Hierarchical decomposition of sphere
   - Good for large-scale geo queries

Recommended: Redis GEOADD/GEORADIUS for simplicity
```

### Finding Nearby Drivers

```python
def find_nearby_drivers(pickup_location, radius_km=5):
    # Get drivers within radius using Redis
    nearby = redis.georadius(
        "drivers:locations",
        pickup_location.lng,
        pickup_location.lat,
        radius_km,
        unit="km",
        withdist=True,
        count=20,
        sort="ASC"
    )

    # Filter available drivers only
    available = []
    for driver_id, distance in nearby:
        driver = get_driver(driver_id)
        if driver.status == "available":
            available.append({
                "driver_id": driver_id,
                "distance": distance,
                "eta": calculate_eta(driver.location, pickup_location)
            })

    return available[:10]  # Top 10 closest
```

---

## 6. Deep Dive: Matching Service

### Matching Algorithm

```
┌─────────────────────────────────────────────────────────────────┐
│                    MATCHING FLOW                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Rider requests ride                                         │
│                │                                                 │
│                ▼                                                 │
│  2. Find nearby available drivers                               │
│     - Query geospatial index                                    │
│     - Filter by availability, ride type                         │
│                │                                                 │
│                ▼                                                 │
│  3. Rank drivers                                                │
│     - ETA to pickup                                             │
│     - Driver rating                                             │
│     - Acceptance rate                                           │
│                │                                                 │
│                ▼                                                 │
│  4. Send ride request to top driver                             │
│     - 15-second timeout to accept                               │
│                │                                                 │
│     ┌─────────┴─────────┐                                       │
│     │                   │                                        │
│     ▼                   ▼                                        │
│  Accepted            Declined/Timeout                           │
│     │                   │                                        │
│     ▼                   ▼                                        │
│  Match complete      Try next driver                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Dispatch Optimization

```
Simple approach: Greedy (closest driver)
  - Easy to implement
  - May not be globally optimal

Advanced: Batch matching
  - Collect requests over short window (5 seconds)
  - Optimize assignments globally
  - Use Hungarian algorithm or similar

  Example:
    Requests: [R1, R2, R3]
    Drivers:  [D1, D2, D3]

    Distance matrix:
           D1    D2    D3
    R1     2km   5km   3km
    R2     4km   1km   6km
    R3     3km   4km   2km

    Optimal: R1→D1, R2→D2, R3→D3 (total: 5km)
    Greedy:  R1→D1, R2→D2, R3→D3 (same, but not always)
```

---

## 7. Deep Dive: Real-time Tracking

### WebSocket Connection

```
┌─────────────────────────────────────────────────────────────────┐
│                    REAL-TIME TRACKING                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Driver App                     Rider App                       │
│      │                              ▲                           │
│      │ Location updates             │ Location updates          │
│      ▼                              │                           │
│  ┌─────────────┐              ┌─────────────┐                  │
│  │  Location   │──── Kafka ──>│  Tracking   │                  │
│  │   Service   │              │   Service   │                  │
│  └─────────────┘              └─────────────┘                  │
│                                     │                           │
│                               WebSocket                         │
│                                     │                           │
│                                     ▼                           │
│                               Rider App                         │
│                                                                  │
│  Flow:                                                          │
│  1. Driver sends location update                                │
│  2. Location Service publishes to Kafka topic: ride_123         │
│  3. Tracking Service subscribed to ride_123                     │
│  4. Tracking Service pushes to Rider via WebSocket              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Connection Management

```
WebSocket server challenges:
  - 1M concurrent connections
  - Sticky sessions needed
  - Connection failover

Solution: Distributed WebSocket with Redis Pub/Sub

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  WS Server  │     │  WS Server  │     │  WS Server  │
│     1       │     │     2       │     │     3       │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    ┌──────▼──────┐
                    │ Redis Pub/  │
                    │    Sub      │
                    └─────────────┘

When driver location updates:
  1. Publish to Redis channel: ride:{ride_id}:location
  2. All WS servers subscribed to relevant channels
  3. Server with rider's connection pushes update
```

---

## 8. Database Design

### Ride Data (PostgreSQL)

```sql
CREATE TABLE rides (
    ride_id UUID PRIMARY KEY,
    rider_id UUID NOT NULL,
    driver_id UUID,
    status VARCHAR(20) NOT NULL,
    pickup_location POINT NOT NULL,
    destination POINT NOT NULL,
    pickup_address TEXT,
    destination_address TEXT,
    fare_amount DECIMAL(10,2),
    distance_km DECIMAL(10,2),
    duration_minutes INT,
    requested_at TIMESTAMP NOT NULL,
    matched_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP,

    CONSTRAINT valid_status CHECK (status IN
      ('requested', 'matching', 'matched', 'driver_arriving',
       'in_progress', 'completed', 'cancelled'))
);

CREATE INDEX idx_rides_rider ON rides(rider_id, requested_at DESC);
CREATE INDEX idx_rides_driver ON rides(driver_id, requested_at DESC);
CREATE INDEX idx_rides_status ON rides(status) WHERE status NOT IN ('completed', 'cancelled');
```

### Driver Location (Redis)

```
# Current location
GEOADD drivers:locations <lng> <lat> <driver_id>

# Driver metadata
HSET driver:<driver_id>
  status "available"
  last_lat 37.7749
  last_lng -122.4194
  updated_at 1705312200

# Active drivers in geohash cell
SADD geohash:9q8yyk <driver_id>
```

---

## 9. Key Trade-offs

```
Trade-off 1: Location Update Frequency
  Chose: Every 4 seconds
  Because: Balance between accuracy and bandwidth/battery
  Note: Can increase during active ride

Trade-off 2: Matching Strategy
  Chose: Greedy (closest available)
  Over: Batch optimization
  Because: Simpler, good enough for most cases
  Note: Can add batch optimization for high-density areas

Trade-off 3: Consistency
  Chose: Strong for ride state, eventual for location
  Because: Ride state is critical, location can be slightly stale

Trade-off 4: WebSocket vs Polling
  Chose: WebSocket for tracking
  Because: Real-time requirement, less overhead
```

---

## 10. Handling Edge Cases

### Driver Goes Offline During Ride

```
Detection:
  - No location update for 2 minutes
  - Driver app reports disconnect

Handling:
  1. Send push notification to driver
  2. If no response in 2 minutes:
     - Mark ride as "driver_lost"
     - Notify rider
     - Attempt to match new driver
  3. Original driver doesn't get charged
```

### Rider Cancels After Match

```
Policy:
  - Free cancellation within 2 minutes
  - Cancellation fee after driver starts traveling

Implementation:
  1. Update ride status to "cancelled"
  2. Notify driver via push notification
  3. Apply cancellation fee if applicable
  4. Driver returns to available pool
```

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    UBER ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Services:                                                       │
│    • Location Service: Handle 500K updates/sec                  │
│    • Matching Service: Find and assign drivers                  │
│    • Ride Service: Manage ride lifecycle                        │
│    • Tracking Service: Real-time location to riders             │
│    • Payment Service: Handle fares and payments                 │
│                                                                  │
│  Data Stores:                                                   │
│    • PostgreSQL: Ride data, user data                           │
│    • Redis: Location cache, geospatial index                    │
│    • Kafka: Location streaming, event processing                │
│    • Cassandra: Location history (optional)                     │
│                                                                  │
│  Key Design Decisions:                                          │
│    • Redis GEOADD for spatial queries                           │
│    • Greedy matching with fallback                              │
│    • WebSocket for real-time tracking                           │
│    • Location update every 4 seconds                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interview Tips

```
Key points to hit:
  1. Location service handling 500K updates/sec
  2. Geospatial indexing approach (Redis GEOADD)
  3. Matching algorithm (greedy vs optimized)
  4. Real-time tracking via WebSocket
  5. Consistency model (strong for rides, eventual for location)

Common follow-ups:
  - How to handle surge pricing?
  - How to optimize for ride pooling?
  - How to handle driver no-shows?
  - How to calculate ETA?
```
