# Food Delivery / DoorDash

Design a food delivery platform like DoorDash, Uber Eats, or Grubhub.

---

## 1. Requirements

### Functional Requirements
```
Customer Features:
  1. Browse restaurants and menus
  2. Search restaurants by cuisine, location
  3. Place orders
  4. Track order in real-time
  5. Pay for orders

Restaurant Features:
  1. Manage menu and availability
  2. Receive and accept orders
  3. Update order status

Driver Features:
  1. Go online/offline
  2. Accept/decline delivery requests
  3. Navigate to restaurant and customer
  4. Complete delivery

Out of Scope:
  - Scheduling future orders
  - Group orders
  - Loyalty programs
  - Driver ratings system
```

### Non-Functional Requirements
```
Scale:
  - 10M daily orders
  - 500K restaurants
  - 2M drivers
  - 50M customers

Performance:
  - Order placement: < 2 seconds
  - Order matching to driver: < 30 seconds
  - Real-time tracking: < 2 second delay

Availability:
  - 99.99% during meal times (critical)

Consistency:
  - Strong for orders and payments
  - Eventual for tracking
```

---

## 2. Estimation

### Traffic
```
Orders:
  10M orders/day ÷ 86,400 ≈ 115 orders/second
  Peak (lunch/dinner, 10x): 1,150 orders/second

Restaurant availability checks:
  Each order checks ~20 restaurants
  115 × 20 = 2,300 reads/second
  Peak: 23,000 reads/second

Driver location updates:
  500K active drivers × 1 update/5 seconds
  = 100,000 updates/second
```

### Storage
```
Order data:
  Per order: ~5 KB (items, addresses, status history)
  10M × 5 KB = 50 GB/day
  1 year: 18 TB

Menu data:
  500K restaurants × 50 items × 1 KB = 25 GB
  (Relatively static, heavy read)
```

---

## 3. API Design

```
Customer APIs:

GET /restaurants?lat=37.77&lng=-122.41&cuisine=italian&limit=20
  Response: {
    "restaurants": [
      {
        "id": "rest123",
        "name": "Tony's Pizza",
        "cuisine": "Italian",
        "rating": 4.5,
        "delivery_time_minutes": 35,
        "delivery_fee": 2.99,
        "distance_miles": 1.2
      }
    ]
  }

GET /restaurants/{id}/menu
  Response: {
    "categories": [
      {
        "name": "Pizzas",
        "items": [
          {
            "id": "item456",
            "name": "Margherita",
            "price": 18.99,
            "description": "...",
            "customizations": [...]
          }
        ]
      }
    ]
  }

POST /orders
  Request: {
    "restaurant_id": "rest123",
    "items": [
      {"item_id": "item456", "quantity": 2, "customizations": [...]}
    ],
    "delivery_address": {...},
    "payment_method_id": "pm_123"
  }
  Response: {
    "order_id": "order789",
    "estimated_delivery": "2024-01-15T19:30:00Z",
    "total": 45.97
  }

GET /orders/{id}
  Response: {
    "order_id": "order789",
    "status": "driver_picking_up",
    "driver": {
      "name": "John",
      "phone": "555-1234",
      "location": {"lat": 37.78, "lng": -122.40}
    },
    "estimated_arrival": "2024-01-15T19:25:00Z"
  }

Driver APIs:

POST /drivers/location
  Request: {"lat": 37.77, "lng": -122.41}

POST /deliveries/{id}/accept
POST /deliveries/{id}/pickup
POST /deliveries/{id}/complete

Restaurant APIs:

POST /orders/{id}/accept
POST /orders/{id}/ready
PATCH /menu/items/{id}
  Request: {"available": false}
```

---

## 4. High-Level Design

```
                              ┌─────────────┐
                              │   Clients   │
                              │(Customer/   │
                              │Driver/Rest) │
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
     │Restaurant │            │   Order    │            │  Driver   │
     │  Service  │            │  Service   │            │  Service  │
     └─────┬─────┘            └──────┬─────┘            └─────┬─────┘
           │                         │                         │
           │                    ┌────▼────┐                    │
           │                    │Matching │                    │
           │                    │ Service │                    │
           │                    └────┬────┘                    │
           │                         │                         │
    ┌──────┴──────┐          ┌───────┴───────┐         ┌──────┴──────┐
    │             │          │               │         │             │
┌───▼───┐   ┌─────▼───┐  ┌───▼───┐    ┌─────▼───┐  ┌──▼────┐  ┌────▼────┐
│ Menu  │   │ Search  │  │ Order │    │ Payment │  │Driver │  │Location │
│ Cache │   │(Elastic)│  │  DB   │    │ Service │  │  DB   │  │  Store  │
└───────┘   └─────────┘  └───────┘    └─────────┘  └───────┘  └─────────┘
```

---

## 5. Deep Dive: Order Flow

### Complete Order Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORDER STATE MACHINE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────┐   ┌─────────────┐   ┌───────────────┐              │
│  │ PLACED │──>│ RESTAURANT  │──>│  PREPARING    │              │
│  │        │   │  CONFIRMED  │   │               │              │
│  └────────┘   └─────────────┘   └───────┬───────┘              │
│       │                                 │                       │
│       │ (timeout)                       ▼                       │
│       ▼                        ┌────────────────┐               │
│  ┌──────────┐                  │ READY_FOR_     │               │
│  │ CANCELLED│                  │ PICKUP         │               │
│  └──────────┘                  └────────┬───────┘               │
│       ▲                                 │                       │
│       │                                 ▼                       │
│       │                        ┌────────────────┐               │
│       │                        │ DRIVER_ASSIGNED│               │
│       │ (any state)            └────────┬───────┘               │
│       │                                 │                       │
│       │                                 ▼                       │
│       │                        ┌────────────────┐               │
│       └────────────────────────│ PICKED_UP      │               │
│                                └────────┬───────┘               │
│                                         │                       │
│                                         ▼                       │
│                                ┌────────────────┐               │
│                                │  DELIVERED     │               │
│                                └────────────────┘               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Order Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORDER PROCESSING                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Customer places order                                       │
│     │                                                           │
│     ▼                                                           │
│  2. Validate order                                              │
│     • Check restaurant is open                                  │
│     • Verify items available                                    │
│     • Calculate totals (items + tax + delivery fee + tip)       │
│     │                                                           │
│     ▼                                                           │
│  3. Process payment (hold, not charge)                          │
│     │                                                           │
│     ▼                                                           │
│  4. Create order record → Status: PLACED                        │
│     │                                                           │
│     ▼                                                           │
│  5. Notify restaurant (push notification)                       │
│     │                                                           │
│     ├──► Restaurant accepts → Status: RESTAURANT_CONFIRMED      │
│     │    │                                                      │
│     │    ▼                                                      │
│     │    Begin preparing food                                   │
│     │    Estimate prep time                                     │
│     │                                                           │
│     └──► Restaurant declines/timeout (5 min)                    │
│          │                                                      │
│          ▼                                                      │
│          Cancel order, refund payment                           │
│                                                                  │
│  6. When ~10 min before ready:                                  │
│     Trigger driver matching                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Deep Dive: Driver Matching

### Matching Algorithm

```
┌─────────────────────────────────────────────────────────────────┐
│                    DRIVER MATCHING                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Goal: Minimize total delivery time while keeping drivers busy  │
│                                                                  │
│  When to match:                                                 │
│    • ~10 minutes before food ready                              │
│    • Consider driver travel time to restaurant                  │
│                                                                  │
│  Matching factors:                                              │
│    1. Distance to restaurant                                    │
│    2. Driver heading/direction                                  │
│    3. Driver's current task queue                               │
│    4. Historical acceptance rate                                │
│    5. Vehicle type (if applicable)                              │
│                                                                  │
│  Simple approach: Greedy matching                               │
│    For each order needing driver:                               │
│      1. Find available drivers within 5 km                      │
│      2. Rank by ETA to restaurant                               │
│      3. Send offer to top driver                                │
│      4. 30-second timeout to accept                             │
│      5. If declined, try next driver                            │
│                                                                  │
│  Advanced: Batch matching                                       │
│    Collect orders over 30-second window                         │
│    Solve assignment problem to minimize total delivery time     │
│    (Hungarian algorithm or similar)                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Driver Availability

```python
def find_available_drivers(restaurant_location, radius_km=5):
    # Query geospatial index
    nearby_drivers = redis.georadius(
        "drivers:locations",
        restaurant_location.lng,
        restaurant_location.lat,
        radius_km,
        unit="km",
        withdist=True,
        count=50,
        sort="ASC"
    )

    available = []
    for driver_id, distance in nearby_drivers:
        driver = get_driver(driver_id)

        # Check availability
        if driver.status != "available":
            continue

        # Check if already has too many orders
        if driver.current_deliveries >= 2:
            continue

        # Calculate ETA to restaurant
        eta = calculate_eta(driver.location, restaurant_location)

        available.append({
            "driver_id": driver_id,
            "distance": distance,
            "eta_minutes": eta,
            "score": calculate_match_score(driver, restaurant_location)
        })

    # Sort by score
    return sorted(available, key=lambda d: d["score"], reverse=True)

def calculate_match_score(driver, restaurant_location):
    # Lower ETA is better
    eta_score = max(0, 30 - driver.eta) / 30

    # Higher acceptance rate is better
    acceptance_score = driver.acceptance_rate

    # Prefer drivers heading toward restaurant
    heading_score = heading_alignment(driver.heading, driver.location, restaurant_location)

    return (eta_score * 0.5) + (acceptance_score * 0.3) + (heading_score * 0.2)
```

### Batched Deliveries (Stacking)

```
Multiple orders to same driver:

Constraints:
  • Max 2-3 orders at a time
  • Orders must be from same restaurant OR nearby restaurants
  • Delivery addresses should be in efficient route

Stacking decision:
  If driver has 1 order from Restaurant A
  And new order comes from Restaurant A (or nearby B)
  And delivery addresses are within 1 km of each other
  → Offer stack to driver

Routing for stacked orders:
  1. Pickup all orders first
  2. Optimize delivery sequence using TSP approximation
  3. Deliver in optimal order
```

---

## 7. Deep Dive: Real-Time Tracking

### Location Updates

```
┌─────────────────────────────────────────────────────────────────┐
│                    REAL-TIME TRACKING                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Driver App:                                                    │
│    • GPS update every 5 seconds (driving)                       │
│    • Every 15 seconds (stationary)                              │
│    • Batch updates for efficiency                               │
│                                                                  │
│  Flow:                                                          │
│  Driver → Location Service → Redis (current) + Kafka (history)  │
│                                    │                             │
│                                    ▼                             │
│                             WebSocket Gateway                    │
│                                    │                             │
│                                    ▼                             │
│                            Customer App                          │
│                                                                  │
│  Customer tracking:                                             │
│    1. Customer opens order tracking                             │
│    2. Client opens WebSocket to gateway                         │
│    3. Gateway subscribes to order:{order_id}:location           │
│    4. Location updates pushed to customer                       │
│    5. Map updates in real-time                                  │
│                                                                  │
│  ETA updates:                                                   │
│    • Recalculate every location update                          │
│    • Consider current traffic                                   │
│    • Push significant changes (> 2 min diff)                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Geofencing for Status Updates

```
Automatic status updates based on location:

Restaurant geofence (100m radius):
  Driver enters → "Driver arriving at restaurant"
  Driver stops for >2 min → Prompt "Mark as picked up?"

Customer geofence (200m radius):
  Driver enters → "Driver nearby"
  Driver stops → Prompt "Mark as delivered?"

Implementation:
  Each location update:
    1. Check distance to restaurant (if not picked up)
    2. Check distance to customer (if picked up)
    3. Trigger notifications/prompts as needed
```

---

## 8. Database Design

### Order Data (PostgreSQL)

```sql
CREATE TABLE orders (
    order_id UUID PRIMARY KEY,
    customer_id UUID NOT NULL,
    restaurant_id UUID NOT NULL,
    driver_id UUID,
    status VARCHAR(30) NOT NULL,

    -- Addresses (denormalized)
    pickup_address JSONB NOT NULL,
    delivery_address JSONB NOT NULL,

    -- Pricing
    subtotal DECIMAL(10,2) NOT NULL,
    tax DECIMAL(10,2) NOT NULL,
    delivery_fee DECIMAL(10,2) NOT NULL,
    tip DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) NOT NULL,

    -- Timing
    placed_at TIMESTAMP NOT NULL,
    estimated_prep_time INT,  -- minutes
    estimated_delivery_at TIMESTAMP,
    picked_up_at TIMESTAMP,
    delivered_at TIMESTAMP,

    -- Payment
    payment_intent_id VARCHAR(100),
    payment_status VARCHAR(20)
);

CREATE TABLE order_items (
    order_id UUID REFERENCES orders(order_id),
    item_id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    customizations JSONB,
    PRIMARY KEY (order_id, item_id)
);

CREATE TABLE order_status_history (
    order_id UUID REFERENCES orders(order_id),
    status VARCHAR(30) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    actor_type VARCHAR(20),  -- customer, restaurant, driver, system
    notes TEXT,
    PRIMARY KEY (order_id, timestamp)
);

CREATE INDEX idx_orders_customer ON orders(customer_id, placed_at DESC);
CREATE INDEX idx_orders_restaurant ON orders(restaurant_id, placed_at DESC);
CREATE INDEX idx_orders_driver ON orders(driver_id, placed_at DESC);
CREATE INDEX idx_orders_status ON orders(status) WHERE status NOT IN ('delivered', 'cancelled');
```

### Driver Location (Redis)

```
Real-time locations:
  GEOADD drivers:locations <lng> <lat> <driver_id>

Driver state:
  HSET driver:<driver_id>
    status "available"           # available, busy, offline
    current_order "order123"
    last_location_at 1705312200
    heading 180
    speed 25

Active orders by area (for matching):
  GEOADD orders:pending <lng> <lat> <order_id>
```

### Restaurant Data (PostgreSQL + Redis Cache)

```sql
CREATE TABLE restaurants (
    restaurant_id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    location GEOMETRY(POINT, 4326) NOT NULL,
    address TEXT NOT NULL,
    cuisine_type VARCHAR(50)[],
    rating DECIMAL(2,1),
    price_level INT,  -- 1-4 ($-$$$$)
    is_open BOOLEAN DEFAULT true,
    prep_time_minutes INT DEFAULT 20
);

CREATE TABLE menu_items (
    item_id UUID PRIMARY KEY,
    restaurant_id UUID REFERENCES restaurants(restaurant_id),
    category VARCHAR(100) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    is_available BOOLEAN DEFAULT true,
    image_url TEXT,
    customization_options JSONB
);

CREATE INDEX idx_restaurants_location ON restaurants USING GIST(location);
CREATE INDEX idx_menu_items_restaurant ON menu_items(restaurant_id);

-- Redis cache for hot data
restaurant:{id}:info → JSON blob
restaurant:{id}:menu → JSON blob (refreshed every 5 min)
restaurant:{id}:availability → Bitmap of available items
```

---

## 9. Key Trade-offs

```
Trade-off 1: Driver Matching Timing
  Chose: Match ~10 min before food ready
  Because: Minimize driver wait time at restaurant
  Risk: Food might be ready early/late
  Mitigation: Dynamic adjustment based on restaurant history

Trade-off 2: Order Batching (Stacking)
  Chose: Allow up to 2 orders per driver
  Because: Efficiency, lower delivery costs
  Impact: Slightly longer delivery for second customer
  Mitigation: Discount for stacked orders

Trade-off 3: Payment Flow
  Chose: Authorize upfront, capture on delivery
  Because: Guarantee funds, flexibility for adjustments
  Complexity: Handle auth expiration for long deliveries

Trade-off 4: Location Update Frequency
  Chose: 5 seconds while driving
  Because: Balance accuracy vs battery/bandwidth
  Interpolate: Client interpolates between updates
```

---

## 10. Handling Edge Cases

### Restaurant Closes Mid-Order

```
Detection:
  - Restaurant marks as closed in app
  - Restaurant doesn't accept order in 5 minutes

Handling:
  1. If order not confirmed:
     - Cancel order automatically
     - Full refund to customer
     - Notify customer

  2. If order confirmed but not picked up:
     - Attempt to contact restaurant
     - If no response in 10 min:
       - Cancel order
       - Full refund
       - Compensate customer with credit
```

### Driver Cancels After Pickup

```
Severity: High - Food is with driver

Handling:
  1. Immediately reassign to new driver
  2. Track original driver's location
  3. New driver picks up from original driver (if possible)
     OR from restaurant (if food needs remake)
  4. Compensate customer for delay
  5. Flag original driver for review
```

### Payment Fails After Delivery

```
Prevention:
  - Pre-authorize payment before order accepted
  - Auth amount includes buffer for tip changes

If capture fails:
  1. Retry 3 times over 24 hours
  2. If still fails:
     - Mark customer account for review
     - Absorb loss (rare)
     - Block future orders until resolved
```

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    FOOD DELIVERY ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Order Flow:                                                    │
│    Customer → Order Service → Restaurant → Driver → Customer    │
│                                                                  │
│  Matching:                                                      │
│    Order Ready → Matching Service → Find Drivers → Assign       │
│                                                                  │
│  Tracking:                                                      │
│    Driver → Location Service → Redis → WebSocket → Customer     │
│                                                                  │
│  Data Stores:                                                   │
│    • PostgreSQL: Orders, users, restaurants                     │
│    • Redis: Driver locations, restaurant cache                  │
│    • Kafka: Events, notifications                               │
│    • Elasticsearch: Restaurant search                           │
│                                                                  │
│  Key Design Decisions:                                          │
│    • Match drivers proactively before food ready                │
│    • Allow order stacking for efficiency                        │
│    • Real-time tracking via WebSocket                           │
│    • Pre-authorize payments before confirmation                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interview Tips

```
Key points to hit:
  1. Order state machine and lifecycle
  2. Driver matching algorithm (timing is crucial)
  3. Real-time tracking architecture
  4. Payment flow (authorize vs capture)
  5. Handling edge cases gracefully

Common follow-ups:
  - How to handle surge pricing?
  - How to optimize for driver earnings?
  - How to predict delivery times accurately?
  - How to handle peak times (dinner rush)?
```
