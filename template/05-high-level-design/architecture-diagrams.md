# Architecture Diagrams

A collection of ready-to-use architecture diagram templates for common system design patterns.

---

## Table of Contents

1. [Basic Web Application](#1-basic-web-application)
2. [Microservices Architecture](#2-microservices-architecture)
3. [Event-Driven Architecture](#3-event-driven-architecture)
4. [CQRS Pattern](#4-cqrs-pattern)
5. [Multi-Region Deployment](#5-multi-region-deployment)
6. [Real-Time Data Processing](#6-real-time-data-processing)
7. [Content Delivery Architecture](#7-content-delivery-architecture)
8. [Mobile Backend Architecture](#8-mobile-backend-architecture)
9. [Data Pipeline Architecture](#9-data-pipeline-architecture)
10. [Serverless Architecture](#10-serverless-architecture)

---

## 1. Basic Web Application

```
┌─────────────────────────────────────────────────────────────────┐
│                         USERS                                    │
│                    (Web Browsers)                                │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               │ HTTPS
                               ▼
                ┌──────────────────────────────┐
                │           CDN                │
                │   (Static Assets: JS/CSS)    │
                └──────────────┬───────────────┘
                               │
                               ▼
                ┌──────────────────────────────┐
                │      Load Balancer           │
                │      (NGINX/ALB)             │
                └──────────────┬───────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
         ┌──────────┐   ┌──────────┐   ┌──────────┐
         │  Web     │   │  Web     │   │  Web     │
         │  Server  │   │  Server  │   │  Server  │
         │  (Node)  │   │  (Node)  │   │  (Node)  │
         └────┬─────┘   └────┬─────┘   └────┬─────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
       ┌───────────┐   ┌──────────┐   ┌──────────┐
       │   Redis   │   │ Primary  │   │  Object  │
       │  (Cache)  │   │ Database │   │ Storage  │
       │           │   │  (RDS)   │   │   (S3)   │
       └───────────┘   └────┬─────┘   └──────────┘
                            │
                            ▼
                       ┌──────────┐
                       │  Read    │
                       │ Replica  │
                       └──────────┘

Components:
- CDN: CloudFront, Cloudflare
- Load Balancer: ALB, NGINX
- Web Servers: Node.js, Python, Go
- Cache: Redis, Memcached
- Database: PostgreSQL, MySQL
- Object Storage: S3, GCS
```

**Use Case**: E-commerce site, blogging platform, SaaS application

**Traffic**: Up to 10,000 requests/second

**Key Features**:
- Stateless application servers
- Read replica for scaling reads
- CDN for static assets
- Redis for session/cache

---

## 2. Microservices Architecture

```
                        ┌─────────────────┐
                        │    API Gateway  │
                        │   (Kong/Envoy)  │
                        └────────┬────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
          ▼                      ▼                      ▼
    ┌──────────┐          ┌──────────┐          ┌──────────┐
    │  User    │          │  Order   │          │ Payment  │
    │ Service  │          │ Service  │          │ Service  │
    └────┬─────┘          └────┬─────┘          └────┬─────┘
         │                     │                     │
         ▼                     ▼                     ▼
    ┌──────────┐          ┌──────────┐          ┌──────────┐
    │  Users   │          │  Orders  │          │ Payments │
    │    DB    │          │    DB    │          │    DB    │
    └──────────┘          └──────────┘          └──────────┘

                ┌────────────────────────────┐
                │    Message Broker          │
                │    (Kafka/RabbitMQ)        │
                └─────────┬──────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  Email   │    │Analytics │    │Inventory │
    │ Service  │    │ Service  │    │ Service  │
    └──────────┘    └──────────┘    └──────────┘

    ┌────────────────────────────────────────┐
    │     Service Mesh (Istio/Linkerd)       │
    │  - Service Discovery                   │
    │  - Load Balancing                      │
    │  - Circuit Breaking                    │
    │  - Mutual TLS                          │
    └────────────────────────────────────────┘

    ┌────────────────────────────────────────┐
    │   Observability Stack                  │
    │  - Logging: ELK/Splunk                 │
    │  - Metrics: Prometheus/Grafana         │
    │  - Tracing: Jaeger/Zipkin              │
    └────────────────────────────────────────┘
```

**Use Case**: Large-scale applications, enterprise systems

**Key Principles**:
- Database per service
- Async communication via message broker
- Service mesh for cross-cutting concerns
- Centralized observability

**Trade-offs**:
- ✓ Independent deployment and scaling
- ✓ Technology diversity
- ✗ Increased complexity
- ✗ Distributed transactions challenging

---

## 3. Event-Driven Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    EVENT PRODUCERS                              │
├────────────────────────────────────────────────────────────────┤
│  Web API  │  Mobile API  │  IoT Devices  │  Scheduled Jobs     │
└─────┬──────────┬──────────────┬──────────────┬─────────────────┘
      │          │              │              │
      └──────────┼──────────────┼──────────────┘
                 │              │
                 ▼              ▼
          ┌───────────────────────────────┐
          │     Event Bus (Kafka)         │
          │                               │
          │  Topic: user.events           │
          │  Topic: order.events          │
          │  Topic: payment.events        │
          └───────────┬───────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Consumer   │ │   Consumer   │ │   Consumer   │
│    Group 1   │ │    Group 2   │ │    Group 3   │
├──────────────┤ ├──────────────┤ ├──────────────┤
│ Email        │ │ Analytics    │ │ Audit        │
│ Notification │ │ Processing   │ │ Logging      │
└──────────────┘ └──────────────┘ └──────────────┘
        │             │             │
        ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Email DB    │ │  Data        │ │  Audit       │
│              │ │  Warehouse   │ │  Store       │
└──────────────┘ └──────────────┘ └──────────────┘

Event Flow Example:
1. User places order → OrderCreated event
2. Payment service processes → PaymentProcessed event
3. Inventory service updates → InventoryReserved event
4. Notification service sends → OrderConfirmation email
```

**Use Case**: Real-time systems, reactive applications, event sourcing

**Key Patterns**:
- Event sourcing: Store state as sequence of events
- CQRS: Separate read/write models
- Saga pattern: Distributed transactions

**Benefits**:
- Loose coupling between services
- Easy to add new consumers
- Natural audit trail
- Scales horizontally

---

## 4. CQRS Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT                                   │
└────────────┬────────────────────────────┬───────────────────────┘
             │                            │
             │ WRITE (Commands)           │ READ (Queries)
             ▼                            ▼
    ┌────────────────┐          ┌────────────────────┐
    │  COMMAND API   │          │     QUERY API      │
    │  (Write Model) │          │   (Read Model)     │
    └────────┬───────┘          └─────────┬──────────┘
             │                            │
             ▼                            ▼
    ┌────────────────┐          ┌────────────────────┐
    │   Command      │          │   Query Handler    │
    │   Handler      │          │                    │
    └────────┬───────┘          │  - Optimized for   │
             │                  │    fast reads      │
             ▼                  │  - Denormalized    │
    ┌────────────────┐          │  - Cached          │
    │  Write DB      │          │                    │
    │  (PostgreSQL)  │          └─────────┬──────────┘
    │                │                    │
    │  - Normalized  │                    ▼
    │  - ACID        │          ┌────────────────────┐
    │  - Source of   │          │   Read DB          │
    │    Truth       │          │   (MongoDB/ES)     │
    └────────┬───────┘          │                    │
             │                  │  - Denormalized    │
             │                  │  - Eventually      │
             ▼                  │    Consistent      │
    ┌────────────────┐          └────────────────────┘
    │  Event Store   │                    ▲
    │  (Kafka)       │                    │
    └────────┬───────┘                    │
             │                            │
             │   Events                   │
             └────────────────────────────┘
                  Sync Process
```

**Use Case**: Complex domains, high read/write throughput differences

**Example Use Cases**:
- E-commerce product catalog (write once, read millions)
- Banking transactions (strict writes, flexible reads)
- Social media feeds (optimized reads)

**Write Side**:
- Handles commands (CreateOrder, UpdateUser)
- Enforces business rules
- Strong consistency
- Publishes events

**Read Side**:
- Handles queries (GetOrderHistory, SearchProducts)
- Optimized for specific use cases
- Eventually consistent
- Multiple read models possible

---

## 5. Multi-Region Deployment

```
┌───────────────────────────────────────────────────────────────────┐
│                    GLOBAL TRAFFIC MANAGER                          │
│              (Route 53, Traffic Manager, Global LB)                │
│                                                                    │
│  Routing Policy: Latency-based / Geolocation / Failover           │
└────────────┬──────────────────────────────────┬───────────────────┘
             │                                  │
             │                                  │
   ┌─────────▼────────────┐         ┌──────────▼──────────┐
   │   US-EAST-1          │         │   EU-WEST-1         │
   │   (Primary)          │         │   (Secondary)       │
   └──────────────────────┘         └─────────────────────┘
             │                                  │
             │                                  │
   ┌─────────▼────────────┐         ┌──────────▼──────────┐
   │  Regional CDN        │         │  Regional CDN       │
   │  (CloudFront)        │         │  (CloudFront)       │
   └─────────┬────────────┘         └──────────┬──────────┘
             │                                  │
   ┌─────────▼────────────┐         ┌──────────▼──────────┐
   │  Load Balancer       │         │  Load Balancer      │
   └─────────┬────────────┘         └──────────┬──────────┘
             │                                  │
   ┌─────────▼────────────┐         ┌──────────▼──────────┐
   │  Application Tier    │         │  Application Tier   │
   │  (Auto-scaling)      │         │  (Auto-scaling)     │
   └─────────┬────────────┘         └──────────┬──────────┘
             │                                  │
   ┌─────────▼────────────┐         ┌──────────▼──────────┐
   │  Primary Database    │◄───────►│  Replica Database   │
   │  (RDS Multi-AZ)      │         │  (Cross-region)     │
   └──────────────────────┘         └─────────────────────┘
             │                                  │
             ▼                                  ▼
   ┌──────────────────────┐         ┌─────────────────────┐
   │  Object Storage      │◄───────►│  Object Storage     │
   │  (S3)                │  Sync   │  (S3)               │
   └──────────────────────┘         └─────────────────────┘

Data Replication Strategies:
1. Active-Passive: All writes to primary, async replication
2. Active-Active: Writes to both regions, conflict resolution needed
3. Read Replicas: Writes to primary, reads from local replica
```

**Use Case**: Global applications, disaster recovery, low latency worldwide

**Considerations**:
- **Data Consistency**: Eventually consistent across regions
- **Failover Time**: RPO (Recovery Point Objective) / RTO (Recovery Time Objective)
- **Cost**: Running resources in multiple regions
- **Compliance**: Data residency requirements

**Routing Strategies**:
- Latency-based: Route to lowest latency region
- Geolocation: Route based on user location
- Failover: Primary/secondary with health checks
- Weighted: Percentage-based traffic distribution

---

## 6. Real-Time Data Processing

```
┌───────────────────────────────────────────────────────────────┐
│                      DATA SOURCES                              │
├───────────────────────────────────────────────────────────────┤
│  Web Clicks │ Mobile Events │ IoT Sensors │ Application Logs │
└──────┬───────────┬────────────────┬──────────────┬───────────┘
       │           │                │              │
       └───────────┼────────────────┼──────────────┘
                   │                │
                   ▼                ▼
          ┌─────────────────────────────────┐
          │    Ingestion Layer              │
          │    (Kafka, Kinesis)             │
          │                                 │
          │  - High throughput              │
          │  - Durable storage              │
          │  - Partitioning                 │
          └──────────┬──────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Stream     │ │   Stream     │ │   Batch      │
│  Processing  │ │  Processing  │ │  Processing  │
│              │ │              │ │              │
│ (Flink/      │ │ (Spark       │ │ (Spark)      │
│  Storm)      │ │  Streaming)  │ │              │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       │ Real-time      │ Near           │ Batch
       │ (<1 sec)       │ Real-time      │ (hourly/daily)
       │                │ (seconds)      │
       ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Hot Path    │ │  Warm Path   │ │  Cold Path   │
│              │ │              │ │              │
│ Redis/       │ │ TimeSeries   │ │ Data         │
│ DynamoDB     │ │ DB           │ │ Warehouse    │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │   Visualization  │
              │   - Dashboards   │
              │   - Alerts       │
              │   - Reports      │
              └──────────────────┘

Processing Types:

Stream Processing:
- Real-time aggregations
- Windowing operations
- Stateful computations
- Event time processing

Batch Processing:
- Historical analysis
- Data warehousing
- ML model training
- Report generation
```

**Use Case**: Analytics platforms, monitoring systems, fraud detection

**Lambda Architecture**:
- **Speed Layer**: Real-time processing (low latency, approximate)
- **Batch Layer**: Batch processing (high latency, accurate)
- **Serving Layer**: Merge results from both layers

**Kappa Architecture**:
- Everything is a stream
- Single processing pipeline
- Reprocess data by replaying stream

---

## 7. Content Delivery Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        END USERS                             │
│               (Global, Millions of requests)                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                     CDN Edge Locations                        │
│              (150+ Points of Presence Globally)               │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ US-West  │  │ US-East  │  │  Europe  │  │   Asia   │    │
│  │  Edge    │  │  Edge    │  │   Edge   │  │   Edge   │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
└───────┼─────────────┼─────────────┼─────────────┼───────────┘
        │             │             │             │
        │             │    Cache    │             │
        │             │     Miss    │             │
        └─────────────┼─────────────┘             │
                      ▼
          ┌───────────────────────┐
          │   Origin Shield       │
          │  (Regional Cache)     │
          │                       │
          │  - Reduces origin     │
          │    load               │
          │  - Collapses requests │
          └───────────┬───────────┘
                      │
                      ▼
          ┌───────────────────────┐
          │   Origin Servers      │
          ├───────────────────────┤
          │                       │
          │  Static:   Dynamic:   │
          │  S3/GCS    App Servers│
          │            + Database │
          └───────────────────────┘

Cache Configuration:

Static Assets:
- JS/CSS/Images: TTL = 1 year
- Versioned URLs: /app.v123.js
- Immutable content
- High cache hit ratio (95%+)

Dynamic Content:
- HTML pages: TTL = 5-60 minutes
- API responses: TTL = 0-5 minutes
- Personalized: No cache or vary by cookie
- Cache-Control headers

Invalidation Strategy:
1. Versioned URLs (preferred)
2. Cache purging by URL
3. Cache purging by tag/key
4. TTL expiration
```

**Use Case**: Media streaming, news websites, software distribution

**CDN Features**:
- **Edge Caching**: Serve content from nearest location
- **Origin Shield**: Intermediate cache layer
- **Image Optimization**: Resize, compress, format conversion
- **Video Streaming**: HLS/DASH, adaptive bitrate
- **DDoS Protection**: Absorb attacks at edge
- **SSL/TLS**: Certificate management at edge

**Performance Impact**:
- Reduce latency: 200ms → 20ms
- Reduce origin load: 90%+ cache hit ratio
- Improve availability: Continue serving during origin issues

---

## 8. Mobile Backend Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    MOBILE CLIENTS                             │
│              (iOS, Android, React Native)                     │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ HTTPS/HTTP2
                         ▼
           ┌─────────────────────────────┐
           │    Mobile API Gateway       │
           │    (Backend for Frontend)   │
           │                             │
           │  - Auth (JWT/OAuth)         │
           │  - Rate limiting            │
           │  - Request aggregation      │
           │  - Response compression     │
           │  - Offline support          │
           └──────────────┬──────────────┘
                          │
     ┌────────────────────┼────────────────────┐
     │                    │                    │
     ▼                    ▼                    ▼
┌──────────┐        ┌──────────┐        ┌──────────┐
│  User    │        │  Content │        │  Push    │
│  Service │        │  Service │        │  Service │
└────┬─────┘        └────┬─────┘        └────┬─────┘
     │                   │                    │
     ▼                   ▼                    ▼
┌──────────┐        ┌──────────┐        ┌──────────┐
│  User    │        │  Content │        │   FCM/   │
│   DB     │        │    DB    │        │   APNS   │
└──────────┘        └────┬─────┘        └──────────┘
                         │
                         ▼
                    ┌──────────┐
                    │   CDN    │
                    │  (Media) │
                    └────┬─────┘
                         │
                         ▼
                    ┌──────────┐
                    │  Object  │
                    │  Storage │
                    └──────────┘

Mobile-Specific Patterns:

1. Request Batching:
   - Combine multiple API calls
   - Reduce network roundtrips
   - GraphQL or custom batch endpoint

2. Data Sync:
   - Delta sync (send only changes)
   - Conflict resolution
   - Last-write-wins or CRDTs

3. Offline First:
   - Local database (SQLite, Realm)
   - Queue mutations when offline
   - Sync when online

4. Push Notifications:
   - FCM (Android)
   - APNS (iOS)
   - Topic-based subscriptions
   - Rich media support

5. Image Optimization:
   - Multiple resolutions
   - WebP format
   - Lazy loading
   - Thumbnail generation
```

**Use Case**: Mobile apps, progressive web apps

**Mobile Backend Considerations**:
- **Bandwidth**: Minimize payload size
- **Battery**: Reduce network requests
- **Latency**: Handle slow networks gracefully
- **Offline**: Support offline mode
- **Security**: Certificate pinning, token refresh

**API Design for Mobile**:
- Versioned APIs (v1, v2)
- Pagination with cursors
- Conditional requests (If-Modified-Since)
- Compression (gzip, brotli)
- GraphQL for flexible queries

---

## 9. Data Pipeline Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                     DATA SOURCES                               │
├───────────────────────────────────────────────────────────────┤
│  Databases │ APIs │ Files │ Streams │ Third-party Services    │
└──────┬─────────┬────────┬──────────┬─────────────────────────┘
       │         │        │          │
       └─────────┼────────┼──────────┘
                 │        │
                 ▼        ▼
        ┌─────────────────────────┐
        │   Data Ingestion        │
        │                         │
        │  Batch:   Stream:       │
        │  - SFTP   - Kafka       │
        │  - S3     - Kinesis     │
        │  - APIs   - Pub/Sub     │
        └─────────┬───────────────┘
                  │
                  ▼
        ┌─────────────────────────┐
        │   Raw Data Lake         │
        │   (S3, ADLS, GCS)       │
        │                         │
        │  - Immutable            │
        │  - Partitioned by date  │
        │  - Compressed (Parquet) │
        └─────────┬───────────────┘
                  │
                  ▼
        ┌─────────────────────────┐
        │   Data Processing       │
        │   (Spark, Airflow)      │
        │                         │
        │  1. Extract             │
        │  2. Transform           │
        │     - Clean             │
        │     - Validate          │
        │     - Enrich            │
        │     - Aggregate         │
        │  3. Load                │
        └─────────┬───────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌──────────────┐   ┌──────────────────┐
│  Curated     │   │   Processed      │
│  Data Lake   │   │   Data Lake      │
│              │   │                  │
│  - Cleaned   │   │  - Aggregated    │
│  - Validated │   │  - Joined        │
└──────┬───────┘   └────────┬─────────┘
       │                    │
       └────────┬───────────┘
                │
                ▼
      ┌─────────────────────┐
      │   Data Warehouse    │
      │   (Snowflake,       │
      │    Redshift,        │
      │    BigQuery)        │
      │                     │
      │  - Star schema      │
      │  - Optimized reads  │
      │  - Aggregations     │
      └──────────┬──────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌──────────────┐  ┌──────────────┐
│   Analytics  │  │  ML Training │
│   - Tableau  │  │  - Feature   │
│   - Looker   │  │    Store     │
│   - PowerBI  │  │  - Models    │
└──────────────┘  └──────────────┘

Orchestration (Apache Airflow):
┌─────────────────────────────────┐
│  DAG: daily_etl_pipeline        │
│                                 │
│  extract_data                   │
│       ↓                         │
│  transform_data                 │
│       ↓                         │
│  load_warehouse                 │
│       ↓                         │
│  run_quality_checks             │
│       ↓                         │
│  update_dashboards              │
└─────────────────────────────────┘
```

**Use Case**: Business intelligence, data science, analytics

**Pipeline Patterns**:
1. **Batch (ETL)**:
   - Scheduled jobs (daily, hourly)
   - Full or incremental loads
   - High throughput

2. **Stream (ELT)**:
   - Real-time processing
   - Load first, transform later
   - Low latency

3. **Lambda**:
   - Both batch and stream
   - Batch for accuracy, stream for speed

**Data Quality**:
- Schema validation
- Data profiling
- Anomaly detection
- Data lineage tracking

**Best Practices**:
- Idempotent pipelines
- Monitoring and alerting
- Data versioning
- Incremental processing
- Partition pruning

---

## 10. Serverless Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT                                  │
│              (Web, Mobile, IoT)                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTPS
                       ▼
            ┌──────────────────────┐
            │    CloudFront CDN    │
            │   (Static Assets)    │
            └──────────┬───────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │    API Gateway       │
            │                      │
            │  - REST/WebSocket    │
            │  - Auth (Cognito)    │
            │  - Rate limiting     │
            │  - Request validation│
            └──────────┬───────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Lambda     │ │   Lambda     │ │   Lambda     │
│   Function   │ │   Function   │ │   Function   │
│   (User)     │ │   (Order)    │ │   (Payment)  │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  DynamoDB    │ │      SQS     │ │     S3       │
│  (NoSQL DB)  │ │   (Queue)    │ │  (Storage)   │
└──────────────┘ └──────┬───────┘ └──────────────┘
                        │
                        ▼
                ┌──────────────┐
                │   Lambda     │
                │   (Worker)   │
                └──────────────┘

Event Sources:
┌─────────────────────────────────────────┐
│  S3 Events → Lambda (Image processing)  │
│  DynamoDB Streams → Lambda (Replication)│
│  EventBridge → Lambda (Scheduled jobs)  │
│  SQS → Lambda (Async processing)        │
│  API Gateway → Lambda (HTTP endpoints)  │
└─────────────────────────────────────────┘

Serverless Patterns:

1. API Backend:
   API Gateway → Lambda → DynamoDB

2. Async Processing:
   S3 Upload → Lambda → Process → S3

3. Event Processing:
   DynamoDB Stream → Lambda → SNS

4. Scheduled Tasks:
   EventBridge → Lambda → Process

5. Real-time Data:
   Kinesis → Lambda → Analytics
```

**Use Case**: Variable workloads, event-driven apps, rapid prototyping

**Serverless Benefits**:
- No server management
- Auto-scaling (0 to millions)
- Pay per execution
- Built-in HA and fault tolerance

**Serverless Limitations**:
- Cold start latency (100-1000ms)
- Execution time limits (15 min AWS Lambda)
- Vendor lock-in
- Debugging complexity

**Cost Model**:
- Pay per request + compute time
- Free tier: 1M requests/month
- Economical for: Sporadic workloads, small apps
- Expensive for: Sustained high traffic

**Best Practices**:
- Keep functions small and focused
- Use environment variables for config
- Implement idempotency
- Monitor with CloudWatch/X-Ray
- Use layers for shared dependencies
- Warm up functions for critical paths

---

## Diagram Usage Guidelines

### When to Use Each Diagram

| Architecture | Scale | Complexity | Team Size | Use Case |
|-------------|-------|------------|-----------|----------|
| Basic Web App | Small-Medium | Low | 1-5 | MVP, Simple CRUD |
| Microservices | Large | High | 10+ | Enterprise, Complex domain |
| Event-Driven | Medium-Large | Medium-High | 5+ | Real-time, Async |
| CQRS | Large | High | 10+ | Read-heavy, Complex queries |
| Multi-Region | Large | High | 10+ | Global, HA required |
| Real-Time | Medium-Large | Medium-High | 5+ | Analytics, Monitoring |
| CDN | Any | Low-Medium | Any | Content delivery, Media |
| Mobile Backend | Medium | Medium | 5+ | Mobile apps |
| Data Pipeline | Medium-Large | Medium | 5+ | Analytics, BI |
| Serverless | Small-Medium | Low-Medium | 1-5 | Rapid dev, Variable load |

### Customization Tips

1. **Start Simple**: Begin with Basic Web App, add complexity as needed
2. **Mix Patterns**: Combine patterns (e.g., Microservices + Event-Driven)
3. **Consider Trade-offs**: More complexity = higher operational overhead
4. **Document Decisions**: Explain why you chose this architecture
5. **Plan for Growth**: Design for current scale + 10x

---

## Next Steps

1. → [Component Overview](component-overview.md) - Detailed component guide
2. → [Design Checklist](design-checklist.md) - Architecture validation
3. → [Deep Dive](../06-deep-dive/) - Implementation details
