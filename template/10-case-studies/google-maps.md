# Google Maps / Navigation

Design a mapping and navigation service like Google Maps or Waze.

---

## 1. Requirements

### Functional Requirements
```
Core Features:
  1. View map (pan, zoom)
  2. Search for places/addresses
  3. Get directions (driving, walking, transit)
  4. Real-time navigation with turn-by-turn
  5. Show traffic conditions

Out of Scope:
  - Street View
  - Indoor maps
  - Business listings/reviews
  - Offline maps (mention briefly)
```

### Non-Functional Requirements
```
Scale:
  - 1B monthly active users
  - 50M navigation sessions per day
  - Map covers entire world

Performance:
  - Map tile load: < 200ms
  - Route calculation: < 2 seconds
  - Location update: Every second during navigation

Availability:
  - 99.99% uptime (critical for navigation)

Accuracy:
  - Route accuracy: Real-time traffic considered
  - ETA accuracy: Within 10% of actual
```

---

## 2. Estimation

### Traffic
```
Map tile requests:
  1B users × 10 tile loads/session × 2 sessions/day
  = 20B tile requests/day
  ≈ 230,000 tiles/second

Navigation requests:
  50M sessions × average 30 min × 1 update/sec
  = 90B location updates/day
  ≈ 1M updates/second

Route calculations:
  50M routes/day ÷ 86,400 ≈ 580 routes/second
  Peak (rush hour, 5x): 2,900 routes/second
```

### Storage
```
Map data:
  Vector data (roads, buildings, POIs): ~50 TB
  Pre-rendered tiles (all zoom levels): ~500 TB
  Traffic data (time-series): ~10 TB

Location history:
  1M updates/sec × 50 bytes × 86,400 sec = 4.3 TB/day
  Keep 7 days: 30 TB
```

### Bandwidth
```
Map tiles:
  230,000 tiles/sec × 20 KB avg = 4.6 GB/second
  CDN handles 95%+ → Origin: 230 MB/second

Navigation updates:
  1M updates/sec × 100 bytes = 100 MB/second ingress
```

---

## 3. API Design

```
Map Tiles:

GET /tiles/{z}/{x}/{y}.{format}
  z: zoom level (0-21)
  x, y: tile coordinates
  format: png, vector (pbf)
  Response: Binary tile data

Search:

GET /search?q=coffee+near+me&location=37.7749,-122.4194&radius=5000
  Response: {
    "results": [
      {
        "place_id": "place123",
        "name": "Blue Bottle Coffee",
        "address": "66 Mint St, San Francisco",
        "location": {"lat": 37.7822, "lng": -122.4050},
        "rating": 4.5,
        "types": ["cafe", "food"]
      }
    ]
  }

Directions:

GET /directions?origin=37.7749,-122.4194&destination=37.3382,-121.8863&mode=driving
  Response: {
    "routes": [
      {
        "summary": "US-101 S",
        "distance_meters": 77000,
        "duration_seconds": 3600,
        "polyline": "encoded_polyline_string",
        "steps": [
          {
            "instruction": "Head south on Market St",
            "distance_meters": 500,
            "duration_seconds": 60,
            "start_location": {...},
            "end_location": {...}
          }
        ]
      }
    ],
    "traffic_conditions": "moderate"
  }

Navigation (WebSocket for real-time):

// Client → Server
{
  "type": "location_update",
  "lat": 37.7749,
  "lng": -122.4194,
  "heading": 180,
  "speed": 45,
  "accuracy": 5
}

// Server → Client
{
  "type": "navigation_update",
  "next_instruction": "In 500 meters, turn right onto Oak St",
  "distance_to_next": 500,
  "eta_seconds": 1800,
  "route_status": "on_route"  // or "rerouting"
}
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
                              │ (Map Tiles) │
                              └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │    Load     │
                              │  Balancer   │
                              └──────┬──────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           │                         │                         │
     ┌─────▼─────┐            ┌──────▼─────┐            ┌─────▼─────┐
     │   Tile    │            │  Routing   │            │  Search   │
     │  Service  │            │  Service   │            │  Service  │
     └─────┬─────┘            └──────┬─────┘            └─────┬─────┘
           │                         │                         │
           │                    ┌────▼────┐                    │
           │                    │ Traffic │                    │
           │                    │ Service │                    │
           │                    └────┬────┘                    │
           │                         │                         │
    ┌──────┴──────┐          ┌───────┴───────┐         ┌──────┴──────┐
    │             │          │               │         │             │
┌───▼───┐   ┌─────▼───┐  ┌───▼───┐    ┌─────▼───┐  ┌──▼────┐  ┌────▼────┐
│ Tile  │   │  Map    │  │ Graph │    │ Traffic │  │ Place │  │  Geo    │
│ Cache │   │  Data   │  │  DB   │    │   DB    │  │  DB   │  │  Index  │
└───────┘   └─────────┘  └───────┘    └─────────┘  └───────┘  └─────────┘
```

---

## 5. Deep Dive: Map Tiles

### Tile System

```
┌─────────────────────────────────────────────────────────────────┐
│                    MAP TILE SYSTEM                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  World divided into tiles at each zoom level:                   │
│                                                                  │
│  Zoom 0: 1 tile (whole world)                                   │
│  Zoom 1: 4 tiles (2×2)                                          │
│  Zoom 2: 16 tiles (4×4)                                         │
│  ...                                                            │
│  Zoom n: 4^n tiles                                              │
│                                                                  │
│  Zoom 21: ~4.4 trillion tiles (but only populated areas)        │
│                                                                  │
│  ┌─────┬─────┐   ┌──┬──┬──┬──┐                                  │
│  │     │     │   │  │  │  │  │                                  │
│  │  0  │  1  │   ├──┼──┼──┼──┤  Zoom level increases            │
│  │     │     │   │  │  │  │  │  More detail per tile            │
│  ├─────┼─────┤   ├──┼──┼──┼──┤                                  │
│  │     │     │   │  │  │  │  │                                  │
│  │  2  │  3  │   ├──┼──┼──┼──┤                                  │
│  │     │     │   │  │  │  │  │                                  │
│  └─────┴─────┘   └──┴──┴──┴──┘                                  │
│    Zoom 1          Zoom 2                                       │
│                                                                  │
│  Tile coordinates: z/x/y                                        │
│  Example: /tiles/15/5241/12661.png                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Tile Types

```
1. Raster Tiles (PNG):
   - Pre-rendered images
   - Fast to serve, cached at CDN
   - Large storage (500 TB+)
   - Different styles require separate tiles

2. Vector Tiles (Protocol Buffers):
   - Raw geometry data
   - Rendered on client
   - Smaller size (~10% of raster)
   - Flexible styling
   - More CPU on client

Current approach: Vector tiles (modern)
   - Fallback to raster for older devices
```

### Tile Generation Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    TILE GENERATION                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Source Data:                                                   │
│    • OpenStreetMap data                                         │
│    • Satellite imagery                                          │
│    • Survey data (roads, buildings)                             │
│    • Partner data (businesses, transit)                         │
│                                                                  │
│  Processing Pipeline:                                           │
│    1. Import raw data → PostGIS database                        │
│    2. Clean and normalize                                       │
│    3. Generate tiles for each zoom level                        │
│       (Mapnik, TileMill, or custom renderer)                    │
│    4. Store tiles in blob storage                               │
│    5. Distribute to CDN                                         │
│                                                                  │
│  Update frequency:                                              │
│    • Major roads: Weekly                                        │
│    • Minor features: Monthly                                    │
│    • Imagery: Yearly                                            │
│                                                                  │
│  On-demand generation:                                          │
│    • Less popular areas generated on request                    │
│    • Cached after first generation                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Deep Dive: Routing Algorithm

### Graph Representation

```
┌─────────────────────────────────────────────────────────────────┐
│                    ROAD NETWORK AS GRAPH                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Nodes: Intersections, road endpoints                           │
│  Edges: Road segments                                           │
│                                                                  │
│  Global road network:                                           │
│    ~500 million nodes                                           │
│    ~1 billion edges                                             │
│                                                                  │
│  Edge properties:                                               │
│    • Length (meters)                                            │
│    • Speed limit                                                │
│    • Road type (highway, local, etc.)                           │
│    • One-way flag                                               │
│    • Turn restrictions                                          │
│    • Current traffic speed                                      │
│                                                                  │
│       Node A ────────── Edge ──────────> Node B                 │
│              {                                                  │
│                length: 500m,                                    │
│                speed_limit: 35mph,                              │
│                type: "local",                                   │
│                current_speed: 25mph                             │
│              }                                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Routing Algorithms

```
1. Dijkstra's Algorithm:
   - Classic shortest path
   - Too slow for global scale
   - O(E log V) complexity

2. A* Algorithm:
   - Dijkstra with heuristic
   - Uses straight-line distance to guide search
   - Better but still too slow for long routes

3. Contraction Hierarchies (CH):
   - Pre-process graph to add "shortcut" edges
   - Query time: O(log n) typical
   - Used by most production systems

   Pre-processing:
     - Contract least important nodes first
     - Add shortcuts to preserve distances
     - Result: hierarchical graph

   Query:
     - Bidirectional search from origin and destination
     - Meet at important nodes
     - Milliseconds for continental routes

4. A* with Landmarks (ALT):
   - Pre-compute distances to landmark nodes
   - Use for better heuristics
   - Good complement to CH
```

### Route Calculation

```python
def calculate_route(origin, destination, mode='driving'):
    # Find nearest nodes to origin/destination
    origin_node = find_nearest_node(origin)
    dest_node = find_nearest_node(destination)

    # Use Contraction Hierarchies for fast routing
    path = ch_query(origin_node, dest_node, mode)

    # Apply current traffic to get accurate times
    path = apply_traffic(path, get_current_traffic())

    # Generate turn-by-turn instructions
    instructions = generate_instructions(path)

    # Encode path as polyline for efficient transfer
    polyline = encode_polyline(path)

    return {
        'polyline': polyline,
        'distance': path.total_distance,
        'duration': path.total_duration,
        'steps': instructions
    }
```

---

## 7. Deep Dive: Traffic System

### Traffic Data Collection

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRAFFIC DATA SOURCES                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Mobile GPS data (primary):                                  │
│     • Anonymous location from Maps users                        │
│     • Speed calculated from movement                            │
│     • Millions of probes per second                             │
│                                                                  │
│  2. Road sensors:                                               │
│     • Government traffic sensors                                │
│     • Inductive loop detectors                                  │
│     • Camera-based counting                                     │
│                                                                  │
│  3. Partner data:                                               │
│     • Ride-share companies (Uber, Lyft)                         │
│     • Delivery fleets                                           │
│     • Transit agencies                                          │
│                                                                  │
│  Processing pipeline:                                           │
│    Raw GPS → Map Matching → Speed Aggregation → Road Segments   │
│                                                                  │
│  Map Matching:                                                  │
│    • GPS points are noisy                                       │
│    • Match to actual road segments                              │
│    • Hidden Markov Model for accuracy                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Traffic Storage

```
Traffic data model:

segment_traffic {
    segment_id: "road_segment_123",
    timestamp: 1705312200,  // 5-minute buckets
    speed_mph: 35,
    free_flow_speed: 45,
    confidence: 0.9,  // Based on sample size
    samples: 150
}

Storage: Time-series database (InfluxDB, TimescaleDB)

Redis for real-time:
  traffic:{segment_id} → current speed, updated every minute

Historical patterns:
  traffic:pattern:{segment_id}:{day_of_week}:{hour} → typical speed
  Used for prediction when no live data
```

### Traffic-Aware Routing

```python
def get_edge_cost(edge, departure_time):
    # Get current traffic speed
    current_speed = redis.get(f"traffic:{edge.segment_id}")

    if current_speed:
        travel_time = edge.length / current_speed
    else:
        # Fall back to historical pattern
        pattern_key = f"traffic:pattern:{edge.segment_id}:{departure_time.weekday()}:{departure_time.hour}"
        historical_speed = redis.get(pattern_key) or edge.speed_limit
        travel_time = edge.length / historical_speed

    return travel_time

def predict_traffic(edge, future_time):
    # Combine current trend + historical pattern
    current = get_current_speed(edge)
    historical = get_historical_speed(edge, future_time)

    # Weight recent data more for near future
    hours_ahead = (future_time - now).hours
    if hours_ahead < 1:
        return current * 0.7 + historical * 0.3
    elif hours_ahead < 3:
        return current * 0.3 + historical * 0.7
    else:
        return historical
```

---

## 8. Deep Dive: Navigation

### Real-Time Navigation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    NAVIGATION SESSION                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. User starts navigation                                      │
│     │                                                           │
│     ├── Calculate initial route                                 │
│     ├── Open WebSocket connection                               │
│     └── Start location updates (1/second)                       │
│                                                                  │
│  2. Location update received                                    │
│     │                                                           │
│     ├── Map match to road segment                               │
│     ├── Check if on route                                       │
│     │   │                                                       │
│     │   ├── On route → Update progress, ETA                     │
│     │   │                                                       │
│     │   └── Off route → Trigger reroute                         │
│     │                                                           │
│     ├── Check for upcoming turns                                │
│     │   • 1000m: "In 1 kilometer, turn right"                   │
│     │   • 500m: "Turn right in 500 meters"                      │
│     │   • 100m: "Turn right"                                    │
│     │                                                           │
│     └── Send navigation update to client                        │
│                                                                  │
│  3. Traffic change detected                                     │
│     │                                                           │
│     ├── Evaluate alternative routes                             │
│     ├── If better route found (saves > 5 min)                   │
│     │   → Notify user, offer reroute                            │
│     └── Update ETA with current traffic                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Navigation State Machine

```
States:
  INITIALIZING → NAVIGATING → ARRIVING → ARRIVED
       ↓              ↓
  REROUTING ←─────────┘
       ↓
  NAVIGATING

Off-route detection:
  - Distance from route > 50 meters
  - And heading differs > 45 degrees
  - For > 5 seconds

  → Trigger reroute from current location
```

---

## 9. Database Design

### Map Data (PostGIS)

```sql
-- Road segments
CREATE TABLE road_segments (
    segment_id UUID PRIMARY KEY,
    way_id BIGINT,  -- OSM way ID
    geometry GEOMETRY(LINESTRING, 4326),
    road_class VARCHAR(20),
    speed_limit INT,
    is_oneway BOOLEAN,
    name VARCHAR(200)
);

CREATE INDEX idx_segments_geom ON road_segments USING GIST(geometry);

-- Graph nodes (intersections)
CREATE TABLE graph_nodes (
    node_id UUID PRIMARY KEY,
    osm_node_id BIGINT,
    location GEOMETRY(POINT, 4326)
);

-- Graph edges (for routing)
CREATE TABLE graph_edges (
    from_node UUID,
    to_node UUID,
    segment_id UUID,
    length_meters FLOAT,
    duration_seconds FLOAT,
    road_class VARCHAR(20),
    PRIMARY KEY (from_node, to_node)
);

-- Places/POIs
CREATE TABLE places (
    place_id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    location GEOMETRY(POINT, 4326),
    address TEXT,
    categories TEXT[],
    metadata JSONB
);

CREATE INDEX idx_places_geom ON places USING GIST(location);
CREATE INDEX idx_places_name ON places USING GIN(to_tsvector('english', name));
```

### Search Index (Elasticsearch)

```json
// Place document
{
  "place_id": "place123",
  "name": "Blue Bottle Coffee",
  "name_suggest": {
    "input": ["Blue Bottle Coffee", "Blue Bottle", "Coffee"],
    "weight": 100
  },
  "location": {
    "lat": 37.7822,
    "lon": -122.4050
  },
  "address": "66 Mint St, San Francisco, CA",
  "categories": ["cafe", "coffee_shop", "food"],
  "rating": 4.5,
  "popularity": 85
}

// Search query with geo-distance
{
  "query": {
    "bool": {
      "must": {
        "multi_match": {
          "query": "coffee",
          "fields": ["name^3", "categories"]
        }
      },
      "filter": {
        "geo_distance": {
          "distance": "5km",
          "location": {"lat": 37.7749, "lon": -122.4194}
        }
      }
    }
  },
  "sort": [
    {"_score": "desc"},
    {"_geo_distance": {"location": {"lat": 37.7749, "lon": -122.4194}}}
  ]
}
```

---

## 10. Key Trade-offs

```
Trade-off 1: Tile Format
  Chose: Vector tiles (primary) with raster fallback
  Because: Smaller size, flexible styling, better zoom
  Cost: More client-side processing

Trade-off 2: Routing Algorithm
  Chose: Contraction Hierarchies
  Because: Fast queries after pre-processing
  Trade-off: Hours of pre-processing when map changes

Trade-off 3: Traffic Freshness
  Chose: 1-minute update granularity
  Because: Balance freshness vs processing cost
  Impact: May miss sudden changes

Trade-off 4: Offline Maps
  Chose: Download entire regions
  Because: Simple, works without connection
  Trade-off: Large downloads, stale data
```

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    GOOGLE MAPS ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Map Display:                                                   │
│    Client → CDN → Tile Service → Tile Storage                   │
│                                                                  │
│  Search:                                                        │
│    Client → Search Service → Elasticsearch → Place DB           │
│                                                                  │
│  Routing:                                                       │
│    Client → Routing Service → Graph DB + Traffic Service        │
│                                                                  │
│  Navigation:                                                    │
│    Client ←→ WebSocket ←→ Navigation Service                    │
│                ↓                                                │
│         Traffic + Routing Services                              │
│                                                                  │
│  Key Design Decisions:                                          │
│    • Vector tiles for flexible, efficient maps                  │
│    • Contraction Hierarchies for fast routing                   │
│    • Real-time traffic from crowd-sourced GPS                   │
│    • WebSocket for live navigation updates                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interview Tips

```
Key points to hit:
  1. Tile system (z/x/y coordinates, zoom levels)
  2. Routing algorithm (CH or A*) - know tradeoffs
  3. Traffic data collection and integration
  4. Real-time navigation with rerouting
  5. Geo-spatial indexing (R-tree, geohash)

Common follow-ups:
  - How to handle routing across country borders?
  - How to optimize for battery life?
  - How to build offline maps feature?
  - How to calculate ETA accurately?
```
