# Security Deep Dive

Comprehensive security considerations for system design.

---

## Security Principles

```
Defense in Depth:
  - Multiple layers of security
  - Assume any layer can fail
  - No single point of compromise

Least Privilege:
  - Minimum permissions needed
  - Time-limited access
  - Regular access reviews

Zero Trust:
  - Never trust, always verify
  - Authenticate every request
  - Encrypt everything
```

---

## Authentication

### Session-Based

```
┌────────┐    1. Login    ┌────────────┐
│ Client │ ──────────────>│   Server   │
│        │<───────────────│            │
└────────┘  2. Set-Cookie │            │
    │       (session_id)  │            │
    │                     └─────┬──────┘
    │                           │
    │                     ┌─────▼──────┐
    │                     │  Session   │
    │                     │   Store    │
    │                     │  (Redis)   │
    │                     └────────────┘
    │
    │  3. Subsequent requests include cookie
    ▼

Pros:
  ✓ Easy to invalidate (delete session)
  ✓ Server controls session data
  ✓ Familiar pattern

Cons:
  ✗ Requires session store
  ✗ Stateful (harder to scale)
  ✗ CSRF vulnerability
```

### Token-Based (JWT)

```
┌────────┐    1. Login    ┌────────────┐
│ Client │ ──────────────>│   Server   │
│        │<───────────────│            │
└────────┘  2. JWT Token  └────────────┘
    │
    │ Store token (localStorage/memory)
    │
    │  3. Request + Authorization: Bearer <token>
    ▼

JWT Structure:
  header.payload.signature

  Header:  { "alg": "RS256", "typ": "JWT" }
  Payload: { "sub": "user123", "exp": 1735689600, "roles": ["user"] }
  Signature: RS256(header.payload, private_key)

Pros:
  ✓ Stateless (scales easily)
  ✓ Cross-domain friendly
  ✓ Contains claims (permissions)

Cons:
  ✗ Can't easily invalidate
  ✗ Larger than session ID
  ✗ Token theft = compromised until expiry
```

### OAuth 2.0 Flows

```
Authorization Code (Web Apps):

┌────────┐    ┌────────────┐    ┌────────────────┐
│ Client │───>│ Auth Server│───>│Resource Server │
└────────┘    └────────────┘    └────────────────┘
     │              │                   │
     │ 1. Redirect  │                   │
     │──────────────>                   │
     │              │                   │
     │ 2. User logs in                  │
     │              │                   │
     │ 3. Auth code │                   │
     │<──────────────                   │
     │              │                   │
     │ 4. Exchange code for tokens      │
     │──────────────>                   │
     │              │                   │
     │ 5. Access token + refresh token  │
     │<──────────────                   │
     │                                  │
     │ 6. API request with access token │
     │─────────────────────────────────>│
     │                                  │
     │ 7. Protected resource            │
     │<─────────────────────────────────│

PKCE (for Mobile/SPA):
  - Adds code_verifier and code_challenge
  - Prevents authorization code interception
```

### Multi-Factor Authentication (MFA)

```
Factors:
  1. Something you know (password)
  2. Something you have (phone, hardware key)
  3. Something you are (fingerprint, face)

Implementation:
  - TOTP (Time-based One-Time Password)
  - SMS (less secure, SIM swap attacks)
  - Push notifications
  - Hardware tokens (YubiKey)

When to require:
  - Login from new device
  - Sensitive operations (password change)
  - Admin access
  - High-value transactions
```

---

## Authorization

### Role-Based Access Control (RBAC)

```
Users ──> Roles ──> Permissions

Example:
  User: john@company.com
  Role: Editor
  Permissions: read, write, publish

┌─────────┐     ┌─────────┐     ┌──────────────┐
│  User   │────>│  Role   │────>│ Permissions  │
│  john   │     │ Editor  │     │ read, write  │
└─────────┘     └─────────┘     │ publish      │
                                └──────────────┘

Pros:
  ✓ Simple to understand
  ✓ Easy to audit
  ✓ Scales with organization

Cons:
  ✗ Role explosion (too many roles)
  ✗ Not context-aware
```

### Attribute-Based Access Control (ABAC)

```
Policy evaluation based on attributes.

Attributes:
  - User: role, department, clearance
  - Resource: type, owner, sensitivity
  - Action: read, write, delete
  - Context: time, location, device

Policy Example:
  ALLOW read ON document
  WHERE user.department == document.department
  AND time.hour BETWEEN 9 AND 17
  AND user.clearance >= document.sensitivity

Pros:
  ✓ Fine-grained control
  ✓ Context-aware
  ✓ Flexible policies

Cons:
  ✗ Complex to implement
  ✗ Harder to audit
  ✗ Performance overhead
```

### API Authorization

```
API Key:
  - Simple, for server-to-server
  - Include in header: X-API-Key: abc123
  - Easy to revoke

OAuth Scopes:
  - Limit access to specific operations
  - User grants scopes during auth
  - Token contains granted scopes

  Example scopes:
    read:user      - Read user profile
    write:posts    - Create/edit posts
    admin:all      - Full admin access

Resource-Based:
  - Check ownership or permissions per resource
  - /users/123/posts - Can user access user 123's posts?
```

---

## Data Protection

### Encryption at Rest

```
Database Encryption:
  - Transparent Data Encryption (TDE)
  - Column-level encryption for sensitive data
  - Key management (AWS KMS, Vault)

Storage Encryption:
  - S3 server-side encryption (SSE-S3, SSE-KMS)
  - EBS volume encryption
  - Disk encryption (LUKS, BitLocker)

Backup Encryption:
  - Encrypt before storing
  - Separate keys from data
  - Secure key backup
```

### Encryption in Transit

```
TLS Configuration:
  - TLS 1.2+ only
  - Strong cipher suites
  - Certificate from trusted CA
  - HSTS header

  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:...;
  ssl_prefer_server_ciphers on;

Internal Traffic:
  - mTLS (mutual TLS) for service-to-service
  - Service mesh (Istio) for automatic mTLS
  - VPN or private network
```

### Secrets Management

```
Don't:
  ✗ Hardcode secrets in code
  ✗ Store in environment variables
  ✗ Commit to version control
  ✗ Log secrets

Do:
  ✓ Use secrets manager (Vault, AWS Secrets Manager)
  ✓ Rotate secrets regularly
  ✓ Audit access to secrets
  ✓ Encrypt secrets at rest

Vault Pattern:
  ┌─────────┐      ┌─────────────┐
  │   App   │─────>│    Vault    │
  │         │<─────│             │
  └─────────┘ secrets└────────────┘
       │                   │
       │               Audit log
       ▼
  Short-lived credentials
```

---

## Network Security

### Defense in Depth

```
┌────────────────────────────────────────────────────────────────┐
│                        Internet                                 │
└─────────────────────────────┬──────────────────────────────────┘
                              │
                      ┌───────▼───────┐
                      │   WAF/DDoS    │  Layer 7 protection
                      │  Protection   │
                      └───────┬───────┘
                              │
                      ┌───────▼───────┐
                      │  Load Balancer│  SSL termination
                      └───────┬───────┘
                              │
                      ┌───────▼───────┐
            DMZ ──────│  API Gateway  │  Rate limiting, auth
                      └───────┬───────┘
                              │
- - - - - - - - - - - - - - - │ - - - - - - - - - - - - - - - - -
                              │
                      ┌───────▼───────┐
          Private ────│  App Servers  │  Business logic
                      └───────┬───────┘
                              │
                      ┌───────▼───────┐
       Data Layer ────│   Database    │  Encryption at rest
                      └───────────────┘
```

### Security Groups / Firewall Rules

```
Principle: Default deny, explicit allow

Web tier:
  Inbound:
    - Port 443 from 0.0.0.0/0 (HTTPS)
    - Port 80 from 0.0.0.0/0 (redirect to HTTPS)
  Outbound:
    - Port 8080 to app-tier (internal)

App tier:
  Inbound:
    - Port 8080 from web-tier only
  Outbound:
    - Port 5432 to db-tier (PostgreSQL)
    - Port 6379 to cache-tier (Redis)

DB tier:
  Inbound:
    - Port 5432 from app-tier only
  Outbound:
    - None (or backup destination)
```

### DDoS Protection

```
Layers of protection:

1. CDN (Cloudflare, CloudFront):
   - Absorb volumetric attacks
   - Global distribution
   - Bot detection

2. WAF (Web Application Firewall):
   - Block malicious patterns
   - Rate limiting
   - SQL injection, XSS protection

3. Load Balancer:
   - Connection limits
   - Slow client protection

4. Application:
   - Rate limiting by user/IP
   - CAPTCHA for suspicious activity
```

---

## Input Validation

### Common Vulnerabilities

```
SQL Injection:
  Bad:  query = f"SELECT * FROM users WHERE id = {user_input}"
  Good: query = "SELECT * FROM users WHERE id = %s", (user_input,)

XSS (Cross-Site Scripting):
  Bad:  <div>{{ user_input }}</div>
  Good: <div>{{ user_input | escape }}</div>

Command Injection:
  Bad:  os.system(f"ls {user_input}")
  Good: subprocess.run(["ls", user_input])

Path Traversal:
  Bad:  open(f"/uploads/{filename}")
  Good: Validate filename, use safe path join
```

### Validation Checklist

```
□ Validate on server (never trust client)
□ Whitelist over blacklist
□ Validate type, length, format, range
□ Sanitize output (escape HTML, SQL)
□ Use parameterized queries
□ Validate file uploads (type, size, name)
□ Rate limit sensitive endpoints
```

---

## Audit and Compliance

### Logging

```
What to log:
  ✓ Authentication events (login, logout, failures)
  ✓ Authorization decisions (access granted/denied)
  ✓ Data access (read sensitive data)
  ✓ Data modifications (create, update, delete)
  ✓ Admin actions
  ✓ Security events (invalid input, attacks)

What NOT to log:
  ✗ Passwords (even hashed)
  ✗ Credit card numbers
  ✗ Personal data (unless required)
  ✗ Session tokens

Log format:
{
  "timestamp": "2024-01-15T10:30:00Z",
  "event": "login_success",
  "user_id": "user123",
  "ip": "1.2.3.4",
  "user_agent": "...",
  "request_id": "req-abc123"
}
```

### Compliance Requirements

```
GDPR (EU Data Privacy):
  - Consent for data collection
  - Right to access, rectify, delete
  - Data breach notification (72 hours)
  - Data processing agreements

HIPAA (US Health Data):
  - PHI protection
  - Access controls
  - Audit trails
  - Encryption

PCI DSS (Payment Cards):
  - Network segmentation
  - Encryption
  - Access control
  - Regular testing

SOC 2:
  - Security
  - Availability
  - Processing integrity
  - Confidentiality
  - Privacy
```

---

## Interview Tips

### Questions to Ask

```
1. What data is sensitive?
   → Determines encryption needs

2. Who are the users?
   → Authentication method

3. What are the access patterns?
   → Authorization model

4. Any compliance requirements?
   → Specific controls needed

5. What's the threat model?
   → Security priorities
```

### Key Points to Discuss

```
✓ Authentication mechanism
✓ Authorization model (RBAC vs ABAC)
✓ Encryption (at rest, in transit)
✓ Secrets management
✓ Input validation
✓ Audit logging
✓ Network security
```

---

## Next Steps

1. → [Observability](observability.md) - Monitoring security
2. → [Fault Tolerance](fault-tolerance.md) - Security + reliability
3. → [Case Studies](../10-case-studies/) - Security in practice
