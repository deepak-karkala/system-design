# API Design Checklist

A comprehensive checklist for designing robust, secure, and scalable APIs.

---

## 1. Authentication & Authorization

### Authentication Methods

```
Method          │ Use Case                    │ Security Level
────────────────┼─────────────────────────────┼───────────────
API Keys        │ Server-to-server            │ Low-Medium
Basic Auth      │ Simple internal APIs        │ Low
OAuth 2.0       │ Third-party access          │ High
JWT             │ Stateless authentication    │ Medium-High
Session Cookies │ Web applications            │ Medium
mTLS            │ Service mesh                │ Very High
```

### OAuth 2.0 Grant Types

```
Grant Type               │ Use Case
─────────────────────────┼────────────────────────────────────
Authorization Code       │ Web apps with backend
Authorization Code + PKCE│ Mobile/SPA apps (recommended)
Client Credentials       │ Machine-to-machine
Implicit (deprecated)    │ Don't use
Password (legacy)        │ First-party apps only
```

### JWT Best Practices

```
DO:
  ✓ Use short expiration times (15 min - 1 hour)
  ✓ Implement refresh token rotation
  ✓ Store sensitive claims in opaque tokens
  ✓ Validate all claims (iss, aud, exp, nbf)
  ✓ Use RS256 or ES256 for signing

DON'T:
  ✗ Store sensitive data in payload
  ✗ Use "none" algorithm
  ✗ Trust tokens without validation
  ✗ Use long-lived tokens without refresh
```

### Checklist
- [ ] Choose authentication method
- [ ] Implement token refresh mechanism
- [ ] Set appropriate token expiration
- [ ] Validate tokens on every request
- [ ] Implement logout/token revocation

---

## 2. Rate Limiting

### Rate Limiting Algorithms

```
Algorithm        │ Description                      │ Pros/Cons
─────────────────┼──────────────────────────────────┼─────────────────────
Fixed Window     │ X requests per time window       │ Simple, but bursty
Sliding Window   │ Rolling window average           │ Smooth, more memory
Token Bucket     │ Tokens replenish over time       │ Allows bursts
Leaky Bucket     │ Constant rate processing         │ Smoothest, no bursts
```

### Rate Limit Implementation

```
Headers to include in responses:
  X-RateLimit-Limit: 100         # Max requests
  X-RateLimit-Remaining: 45      # Requests left
  X-RateLimit-Reset: 1640000000  # Unix timestamp of reset
  Retry-After: 60                # Seconds (if 429)

Response when exceeded:
  HTTP 429 Too Many Requests
  {
    "error": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Try again in 60 seconds.",
    "retry_after": 60
  }
```

### Rate Limiting Strategies

```
By Entity:
  - Per user (authenticated)
  - Per IP (anonymous)
  - Per API key
  - Per organization/tenant

By Scope:
  - Global (all endpoints)
  - Per endpoint
  - Per operation type (read vs write)

Tiered Limits:
  Free:       100 requests/hour
  Pro:        1,000 requests/hour
  Enterprise: 10,000 requests/hour
```

### Checklist
- [ ] Choose rate limiting algorithm
- [ ] Define limits per tier/user type
- [ ] Include rate limit headers
- [ ] Implement graceful degradation
- [ ] Consider distributed rate limiting (Redis)

---

## 3. Pagination

### Pagination Strategies

```
Strategy        │ Pros                        │ Cons
────────────────┼─────────────────────────────┼─────────────────────
Offset-based    │ Simple, random access       │ Slow on large offsets
Cursor-based    │ Consistent, performant      │ No random access
Keyset/Seek     │ Very fast, stable           │ Requires ordered key
```

### Offset Pagination

```
Request:
  GET /users?limit=20&offset=40

Response:
  {
    "data": [...],
    "pagination": {
      "limit": 20,
      "offset": 40,
      "total": 1000,
      "has_more": true
    }
  }

Problem: SELECT * FROM users LIMIT 20 OFFSET 10000
         → Scans 10,000 rows before returning 20
```

### Cursor Pagination (Recommended)

```
Request:
  GET /users?limit=20&cursor=eyJpZCI6MTAwfQ

Response:
  {
    "data": [...],
    "pagination": {
      "limit": 20,
      "next_cursor": "eyJpZCI6MTIwfQ",
      "has_more": true
    }
  }

Cursor is typically base64-encoded:
  {"id": 100, "created_at": "2024-01-01"}
```

### Checklist
- [ ] Choose pagination strategy
- [ ] Set sensible default and max limits
- [ ] Include pagination metadata in response
- [ ] Handle edge cases (empty, last page)
- [ ] Consider sort order stability

---

## 4. Versioning

### Versioning Strategies

```
Strategy         │ Example                    │ Pros/Cons
─────────────────┼────────────────────────────┼────────────────────
URL Path         │ /v1/users                  │ Explicit, easy caching
Query Parameter  │ /users?version=1           │ Less clean
Custom Header    │ X-API-Version: 1           │ Clean URLs, less discoverable
Accept Header    │ Accept: application/vnd... │ REST-correct, complex
```

### URL Path Versioning (Most Common)

```
Current version:
  GET /v2/users/123

Deprecated version (with sunset warning):
  GET /v1/users/123

  Response Headers:
    Deprecation: true
    Sunset: Sat, 01 Jan 2025 00:00:00 GMT
    Link: </v2/users/123>; rel="successor-version"
```

### Versioning Best Practices

```
DO:
  ✓ Version from day one
  ✓ Support at least 2 versions
  ✓ Provide clear deprecation timeline
  ✓ Document breaking vs non-breaking changes
  ✓ Use semantic versioning concepts

Breaking Changes (require new version):
  - Removing endpoints
  - Removing fields
  - Changing field types
  - Changing authentication

Non-Breaking (can add to existing version):
  - Adding new endpoints
  - Adding optional fields
  - Adding new enum values
```

### Checklist
- [ ] Choose versioning strategy
- [ ] Document deprecation policy
- [ ] Set up version sunset process
- [ ] Test backward compatibility
- [ ] Communicate changes to consumers

---

## 5. Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      },
      {
        "field": "age",
        "message": "Must be a positive integer"
      }
    ],
    "request_id": "req_abc123",
    "documentation_url": "https://api.example.com/docs/errors#VALIDATION_ERROR"
  }
}
```

### Error Categories

```
Category          │ HTTP Status │ Example
──────────────────┼─────────────┼────────────────────────────
Validation        │ 400         │ Invalid email format
Authentication    │ 401         │ Missing or invalid token
Authorization     │ 403         │ Insufficient permissions
Not Found         │ 404         │ Resource doesn't exist
Conflict          │ 409         │ Duplicate email
Rate Limit        │ 429         │ Too many requests
Internal          │ 500         │ Unexpected server error
Unavailable       │ 503         │ Service temporarily down
```

### Error Handling Best Practices

```
DO:
  ✓ Use appropriate HTTP status codes
  ✓ Include machine-readable error codes
  ✓ Provide human-readable messages
  ✓ Include request ID for debugging
  ✓ Log errors with context

DON'T:
  ✗ Expose stack traces in production
  ✗ Reveal sensitive data in errors
  ✗ Return 200 for errors
  ✗ Use vague error messages
```

### Checklist
- [ ] Define error response schema
- [ ] Map exceptions to HTTP status codes
- [ ] Create error code catalog
- [ ] Include request IDs for tracing
- [ ] Set up error monitoring/alerting

---

## 6. Request/Response Design

### Request Best Practices

```
Content-Type Headers:
  application/json           # Default for JSON
  multipart/form-data       # File uploads
  application/x-www-form-urlencoded  # Form data

Accept Headers:
  Accept: application/json  # Request JSON response
  Accept-Encoding: gzip     # Enable compression
```

### Response Best Practices

```
Standard Response Envelope:
  {
    "data": { ... },           # Main payload
    "meta": {                  # Metadata
      "request_id": "...",
      "timestamp": "..."
    }
  }

Collection Response:
  {
    "data": [ ... ],
    "pagination": { ... },
    "meta": { ... }
  }
```

### Field Naming Conventions

```
Style         │ Example              │ Common Use
──────────────┼──────────────────────┼─────────────
snake_case    │ user_name, created_at│ Python, Ruby
camelCase     │ userName, createdAt  │ JavaScript
PascalCase    │ UserName, CreatedAt  │ .NET
kebab-case    │ user-name            │ URLs only

Recommendation: Pick one and be consistent
```

### Checklist
- [ ] Define response envelope structure
- [ ] Choose naming convention
- [ ] Document all request/response schemas
- [ ] Implement request validation
- [ ] Enable response compression

---

## 7. Idempotency

### What is Idempotency?

```
An operation is idempotent if making the same request
multiple times has the same effect as making it once.

Idempotent by default:
  GET    - Reading data
  PUT    - Replace resource
  DELETE - Delete resource

Not idempotent:
  POST   - Create resource (duplicates possible)
  PATCH  - May not be (increment operations)
```

### Idempotency Keys

```
Request:
  POST /payments
  Idempotency-Key: unique-client-generated-key-123

  {
    "amount": 100,
    "currency": "USD"
  }

Server behavior:
  1. Check if idempotency key exists in store
  2. If exists: return cached response
  3. If not: process request, store result with key
  4. Key expires after 24 hours
```

### Implementation

```
Storage: Redis with TTL
  Key: idempotency:{key}
  Value: {status, response_body, response_code}
  TTL: 24 hours

Flow:
  1. Client sends request with Idempotency-Key header
  2. Server checks Redis for key
  3. If found and completed: return cached response
  4. If found and in-progress: return 409 Conflict
  5. If not found: process and store
```

### Checklist
- [ ] Identify non-idempotent operations
- [ ] Implement idempotency key storage
- [ ] Set appropriate TTL
- [ ] Handle concurrent requests
- [ ] Document idempotency behavior

---

## 8. Security Considerations

### Security Checklist

```
Transport:
  [ ] HTTPS only (redirect HTTP)
  [ ] TLS 1.2+ required
  [ ] HSTS header enabled

Input Validation:
  [ ] Validate all input parameters
  [ ] Sanitize strings (XSS prevention)
  [ ] Parameterized queries (SQL injection)
  [ ] File upload validation

Output:
  [ ] Don't expose internal errors
  [ ] Don't include sensitive data
  [ ] Set appropriate CORS headers

Headers:
  [ ] X-Content-Type-Options: nosniff
  [ ] X-Frame-Options: DENY
  [ ] Content-Security-Policy
  [ ] X-XSS-Protection: 1; mode=block
```

### CORS Configuration

```
For public APIs:
  Access-Control-Allow-Origin: *

For restricted access:
  Access-Control-Allow-Origin: https://trusted-domain.com
  Access-Control-Allow-Methods: GET, POST, PUT, DELETE
  Access-Control-Allow-Headers: Authorization, Content-Type
  Access-Control-Max-Age: 86400
```

### Checklist
- [ ] Enable HTTPS only
- [ ] Configure CORS properly
- [ ] Implement input validation
- [ ] Add security headers
- [ ] Conduct security review

---

## 9. Documentation

### What to Document

```
Essential:
  - Authentication methods
  - Endpoint reference (method, URL, params)
  - Request/response examples
  - Error codes and meanings
  - Rate limits
  - Versioning policy

Nice to Have:
  - SDKs and code samples
  - Interactive API explorer
  - Changelog
  - Migration guides
  - Webhooks documentation
```

### OpenAPI Specification Example

```yaml
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0

paths:
  /users/{id}:
    get:
      summary: Get user by ID
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: User found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          description: User not found

components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        email:
          type: string
          format: email
```

### Checklist
- [ ] Write OpenAPI/Swagger spec
- [ ] Create getting started guide
- [ ] Document authentication flow
- [ ] Provide code examples
- [ ] Keep docs updated with releases

---

## Master Checklist Summary

```
Category           │ Key Items
───────────────────┼────────────────────────────────────────────
Authentication     │ Method, tokens, refresh, revocation
Rate Limiting      │ Algorithm, limits, headers, storage
Pagination         │ Strategy, limits, metadata
Versioning         │ Strategy, deprecation policy
Error Handling     │ Schema, codes, request IDs
Request/Response   │ Envelope, naming, validation
Idempotency        │ Keys, storage, TTL
Security           │ HTTPS, CORS, headers, validation
Documentation      │ OpenAPI, examples, guides
```

---

## Next Steps

1. → [API Examples](api-examples.md) - See these concepts in practice
2. → [Data Model](../04-data-model/) - Design your data layer
3. → [High-Level Design](../05-high-level-design/) - Architect the full system
