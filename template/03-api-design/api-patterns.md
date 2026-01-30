# API Design Patterns

Choosing the right API style is crucial for system design. This guide covers REST, GraphQL, gRPC, and WebSockets.

---

## API Style Comparison

```
┌──────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ Aspect       │ REST        │ GraphQL     │ gRPC        │ WebSocket   │
├──────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ Protocol     │ HTTP        │ HTTP        │ HTTP/2      │ TCP         │
│ Format       │ JSON/XML    │ JSON        │ Protobuf    │ Any         │
│ Communication│ Request-Resp│ Request-Resp│ Request-Resp│ Bidirectional│
│ Typing       │ Loose       │ Strong      │ Strong      │ Loose       │
│ Caching      │ HTTP native │ Complex     │ Limited     │ None        │
│ Browser      │ Native      │ Native      │ Limited     │ Native      │
│ Learning     │ Easy        │ Medium      │ Medium      │ Easy        │
└──────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
```

---

## REST (Representational State Transfer)

### Overview
REST is the most widely used API style, using HTTP methods to operate on resources.

### Core Principles
```
1. Stateless: Each request contains all information needed
2. Resource-based: URLs represent resources, not actions
3. HTTP methods: Use verbs for operations (GET, POST, PUT, DELETE)
4. Representations: Resources can have multiple formats (JSON, XML)
```

### HTTP Methods
```
Method  │ Purpose              │ Idempotent │ Safe │ Request Body
────────┼──────────────────────┼────────────┼──────┼──────────────
GET     │ Read resource        │ Yes        │ Yes  │ No
POST    │ Create resource      │ No         │ No   │ Yes
PUT     │ Replace resource     │ Yes        │ No   │ Yes
PATCH   │ Partial update       │ No         │ No   │ Yes
DELETE  │ Delete resource      │ Yes        │ No   │ No
```

### URL Design Best Practices
```
Good:
  GET    /users                 # List users
  GET    /users/123             # Get user 123
  POST   /users                 # Create user
  PUT    /users/123             # Update user 123
  DELETE /users/123             # Delete user 123
  GET    /users/123/orders      # Get user's orders
  POST   /users/123/orders      # Create order for user

Bad:
  GET    /getUsers              # Verb in URL
  POST   /createUser            # Verb in URL
  GET    /users/123/getOrders   # Verb in URL
```

### Response Status Codes
```
2xx Success:
  200 OK           - Request succeeded
  201 Created      - Resource created
  204 No Content   - Success, no body (DELETE)

3xx Redirection:
  301 Moved        - Permanent redirect
  304 Not Modified - Cached response valid

4xx Client Error:
  400 Bad Request  - Invalid request syntax
  401 Unauthorized - Authentication required
  403 Forbidden    - Authenticated but not allowed
  404 Not Found    - Resource doesn't exist
  409 Conflict     - Resource conflict (duplicate)
  429 Too Many     - Rate limit exceeded

5xx Server Error:
  500 Internal     - Server error
  502 Bad Gateway  - Upstream error
  503 Unavailable  - Service temporarily down
  504 Timeout      - Upstream timeout
```

### When to Use REST
```
✓ Public APIs (broad compatibility)
✓ CRUD operations on resources
✓ Cacheable data (HTTP caching)
✓ Simple, well-understood domain
✓ Browser-based clients

✗ Real-time requirements
✗ Complex, nested queries
✗ Bandwidth-constrained mobile apps
✗ Microservices with strict contracts
```

---

## GraphQL

### Overview
GraphQL is a query language for APIs that lets clients request exactly the data they need.

### Core Concepts
```
Schema: Defines types and operations
Query: Read operations
Mutation: Write operations
Subscription: Real-time updates
Resolver: Function that fetches data for a field
```

### Example Schema
```graphql
type User {
  id: ID!
  name: String!
  email: String!
  posts: [Post!]!
}

type Post {
  id: ID!
  title: String!
  content: String!
  author: User!
  comments: [Comment!]!
}

type Query {
  user(id: ID!): User
  users(limit: Int, offset: Int): [User!]!
  post(id: ID!): Post
}

type Mutation {
  createUser(name: String!, email: String!): User!
  createPost(title: String!, content: String!, authorId: ID!): Post!
}
```

### Query Example
```graphql
# Client requests exactly what they need
query {
  user(id: "123") {
    name
    posts {
      title
      comments {
        content
      }
    }
  }
}

# Response matches query shape
{
  "data": {
    "user": {
      "name": "John",
      "posts": [
        {
          "title": "My Post",
          "comments": [
            { "content": "Great post!" }
          ]
        }
      ]
    }
  }
}
```

### Advantages
```
✓ Flexible queries (no over-fetching)
✓ Single endpoint
✓ Strongly typed schema
✓ Self-documenting (introspection)
✓ Reduced round trips (nested data in one request)
✓ Easier API evolution (add fields, deprecate old ones)
```

### Challenges
```
✗ Complex caching (no HTTP caching)
✗ Query complexity attacks (N+1, deep nesting)
✗ File uploads (not native)
✗ Steeper learning curve
✗ Potential for expensive queries
```

### Security Considerations
```
Query Depth Limiting:
  - Limit nesting level (e.g., max 5 levels)

Query Complexity:
  - Assign cost to fields
  - Reject queries exceeding threshold

Rate Limiting:
  - By query complexity, not just requests
  - Consider query-based quotas

Persisted Queries:
  - Whitelist allowed queries
  - Reduce parsing overhead
```

### When to Use GraphQL
```
✓ Mobile apps (bandwidth optimization)
✓ Complex, nested data models
✓ Rapid frontend iteration
✓ Multiple clients with different needs
✓ Federation across microservices

✗ Simple CRUD operations
✗ File-heavy operations
✗ Strict caching requirements
✗ Simple backend-to-backend calls
```

---

## gRPC

### Overview
gRPC is a high-performance RPC framework using Protocol Buffers for serialization.

### Core Concepts
```
Protocol Buffers: Binary serialization format
Service Definition: Interface in .proto file
Streaming: Bidirectional streaming support
Code Generation: Auto-generated client/server stubs
```

### Example Proto Definition
```protobuf
syntax = "proto3";

package userservice;

service UserService {
  // Unary RPC
  rpc GetUser(GetUserRequest) returns (User);

  // Server streaming
  rpc ListUsers(ListUsersRequest) returns (stream User);

  // Client streaming
  rpc CreateUsers(stream CreateUserRequest) returns (CreateUsersResponse);

  // Bidirectional streaming
  rpc Chat(stream ChatMessage) returns (stream ChatMessage);
}

message User {
  string id = 1;
  string name = 2;
  string email = 3;
  repeated string roles = 4;
}

message GetUserRequest {
  string id = 1;
}
```

### Communication Patterns
```
1. Unary RPC:
   Client sends one request, server returns one response
   client ──request──> server
   client <──response── server

2. Server Streaming:
   Client sends one request, server returns stream
   client ──request──> server
   client <──response1── server
   client <──response2── server
   client <──response3── server

3. Client Streaming:
   Client sends stream, server returns one response
   client ──request1──> server
   client ──request2──> server
   client <──response── server

4. Bidirectional Streaming:
   Both sides send streams independently
   client ←→ server (both streaming)
```

### Performance Comparison
```
Format       │ Size (bytes) │ Serialize (μs) │ Deserialize (μs)
─────────────┼──────────────┼────────────────┼─────────────────
JSON         │ 1000         │ 50             │ 60
Protobuf     │ 450          │ 15             │ 10
MessagePack  │ 700          │ 30             │ 25
```

### When to Use gRPC
```
✓ Microservices communication
✓ Low latency requirements
✓ Streaming data (video, real-time)
✓ Polyglot environments
✓ Strong typing needed
✓ Mobile clients (smaller payloads)

✗ Browser clients (limited support)
✗ Public APIs (less familiar)
✗ Human-readable debugging needed
✗ Simple request-response
```

---

## WebSockets

### Overview
WebSockets provide full-duplex, persistent connections for real-time communication.

### Connection Lifecycle
```
1. Handshake (HTTP Upgrade):
   Client: GET /chat HTTP/1.1
           Upgrade: websocket
           Connection: Upgrade

   Server: HTTP/1.1 101 Switching Protocols
           Upgrade: websocket

2. Data Transfer:
   ←→ Bidirectional messages
   ←→ Text or binary frames

3. Close:
   Either side can initiate close
```

### Use Cases
```
Real-time Applications:
  - Chat/messaging
  - Live notifications
  - Collaborative editing
  - Live sports scores
  - Stock tickers
  - Gaming

Streaming:
  - Live video/audio
  - Log streaming
  - IoT sensor data
```

### Scaling Challenges
```
Problem: WebSockets are stateful
- Each connection is persistent
- Load balancer needs sticky sessions
- Server state must be managed

Solutions:
1. Sticky Sessions:
   - Route client to same server
   - Use client IP or cookie

2. Pub/Sub Backend:
   - Redis pub/sub
   - Kafka
   - Servers subscribe to channels

3. Connection State Store:
   - Redis: connection → server mapping
   - Central state for failover
```

### Architecture Pattern
```
                         ┌───────────────┐
                         │   Pub/Sub     │
                         │   (Redis)     │
                         └───────┬───────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
       ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐
       │  WS Server  │    │  WS Server  │    │  WS Server  │
       │   (Node)    │    │   (Node)    │    │   (Node)    │
       └──────▲──────┘    └──────▲──────┘    └──────▲──────┘
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 │
                         ┌───────▼───────┐
                         │     Load      │
                         │   Balancer    │
                         │  (Sticky)     │
                         └───────▲───────┘
                                 │
                         ┌───────▼───────┐
                         │    Clients    │
                         └───────────────┘
```

### When to Use WebSockets
```
✓ Real-time bidirectional communication
✓ High-frequency updates
✓ Push notifications (server-initiated)
✓ Collaborative features
✓ Live streaming

✗ Request-response patterns
✗ Infrequent updates (use SSE or polling)
✗ RESTful resource operations
✗ Stateless architectures
```

---

## Decision Matrix: Choosing an API Style

```
Requirement              │ REST │ GraphQL │ gRPC │ WebSocket
─────────────────────────┼──────┼─────────┼──────┼──────────
Public API               │ ★★★  │ ★★      │ ★    │ ★
Internal microservices   │ ★★   │ ★       │ ★★★  │ ★
Mobile optimization      │ ★    │ ★★★     │ ★★★  │ ★★
Real-time updates        │ ★    │ ★       │ ★★   │ ★★★
Complex queries          │ ★    │ ★★★     │ ★    │ ★
Strong typing            │ ★    │ ★★★     │ ★★★  │ ★
Browser support          │ ★★★  │ ★★★     │ ★    │ ★★★
Caching                  │ ★★★  │ ★       │ ★    │ ✗
Streaming                │ ✗    │ ★       │ ★★★  │ ★★★
Learning curve           │ Easy │ Medium  │ Medium│ Easy
```

---

## Hybrid Approaches

Many systems use multiple API styles:

```
Example: E-commerce Platform

External (Public):
  └── REST API for third-party integrations

Customer-Facing:
  └── GraphQL for web/mobile apps
      (flexible product queries)

Internal:
  └── gRPC for microservice communication
      (inventory, pricing, orders)

Real-time:
  └── WebSockets for live updates
      (order tracking, chat support)
```

---

## Next Steps

1. → [API Checklist](api-checklist.md) - Detailed design considerations
2. → [API Examples](api-examples.md) - Worked examples
3. → [Data Model](../04-data-model/) - Design your data layer
