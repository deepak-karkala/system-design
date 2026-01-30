# System Design Case Study Template

Use this template to practice system design for any system.

---

## System: [Name]

### 1. Requirements

#### Functional Requirements
```
Core Features:
  1. [Feature 1]
  2. [Feature 2]
  3. [Feature 3]

Out of Scope:
  - [Feature X]
  - [Feature Y]
```

#### Non-Functional Requirements
```
Scale:
  - DAU: [X million]
  - Total users: [Y million]

Performance:
  - Latency: P99 < [X]ms
  - Availability: [99.X]%

Consistency:
  - [Strong/Eventual] for [data type]
```

---

### 2. Estimation

#### Traffic
```
Read operations:
  [X]M users × [Y] reads/user = [Z]M reads/day
  QPS: [Z]M ÷ 86,400 = [A] QPS
  Peak: [A] × 3 = [B] QPS

Write operations:
  [X]M users × [Y] writes/user = [Z]M writes/day
  QPS: [Z]M ÷ 86,400 = [A] QPS
  Peak: [A] × 3 = [B] QPS

Read:Write Ratio = [X:Y]
```

#### Storage
```
Data per [entity]:
  - [Field 1]: [X] bytes
  - [Field 2]: [Y] bytes
  - Total: [Z] bytes

Daily storage:
  [A] objects × [Z] bytes = [B] GB/day

5-year storage:
  [B] GB × 365 × 5 = [C] TB
```

#### Bandwidth
```
Ingress: [X] TB/day
Egress: [Y] TB/day
Peak: [Z] Gbps
```

---

### 3. API Design

```
[METHOD] /[resource]
  Request: { ... }
  Response: { ... }

[METHOD] /[resource]
  Request: { ... }
  Response: { ... }
```

---

### 4. High-Level Design

```
[Draw ASCII diagram here]

                              ┌─────────────┐
                              │   Clients   │
                              └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │     CDN     │
                              └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │     LB      │
                              └──────┬──────┘
                                     │
                         ┌───────────┼───────────┐
                         │           │           │
                    ┌────▼────┐ ┌────▼────┐ ┌────▼────┐
                    │Service A│ │Service B│ │Service C│
                    └────┬────┘ └────┬────┘ └────┬────┘
                         │           │           │
                         └───────────┼───────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
               ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
               │  Cache  │      │   DB    │      │  Queue  │
               └─────────┘      └─────────┘      └────┬────┘
                                                      │
                                                 ┌────▼────┐
                                                 │ Workers │
                                                 └─────────┘
```

---

### 5. Data Model

#### Database Selection
```
Primary DB: [PostgreSQL/MongoDB/etc.]
Rationale: [Why this choice]

Cache: [Redis]
Rationale: [Why]

Other storage: [S3, Elasticsearch, etc.]
```

#### Schema
```sql
-- Example SQL schema
CREATE TABLE [table_name] (
    id BIGINT PRIMARY KEY,
    [column] [TYPE],
    created_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_[name] ON [table]([columns]);
```

---

### 6. Deep Dive

#### Component 1: [Name]
```
Challenge: [What problem]
Solution: [How we solve it]
Trade-off: [What we sacrifice]
```

#### Component 2: [Name]
```
Challenge: [What problem]
Solution: [How we solve it]
Trade-off: [What we sacrifice]
```

---

### 7. Key Trade-offs

```
Trade-off 1: [Name]
  Chose: [Option A]
  Over: [Option B]
  Because: [Reasoning]

Trade-off 2: [Name]
  Chose: [Option A]
  Over: [Option B]
  Because: [Reasoning]
```

---

### 8. Failure Handling

```
Failure Mode 1: [Component] fails
  Detection: [How we detect]
  Recovery: [How we recover]

Failure Mode 2: [Component] fails
  Detection: [How we detect]
  Recovery: [How we recover]
```

---

### 9. Future Improvements

```
1. [Improvement 1]
2. [Improvement 2]
3. [Improvement 3]
```

---

## Checklist

```
□ Requirements clarified
□ Estimation complete
□ API defined
□ High-level design drawn
□ Database selected and schema designed
□ Deep dive on 2-3 components
□ Trade-offs discussed
□ Failure handling covered
□ Future improvements mentioned
```
