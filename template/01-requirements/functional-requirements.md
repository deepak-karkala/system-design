# Functional Requirements

Functional requirements define **what** the system must do - the features, capabilities, and behaviors that users expect.

---

## Overview

Functional requirements answer: "What should this system do?"

They describe:
- Core features and operations
- User interactions and workflows
- Data inputs and outputs
- Business rules and logic

---

## Framework for Gathering Functional Requirements

### 1. Identify Users and Actors

**Questions to Ask:**
- Who are the primary users of this system?
- Are there different user types/roles with different needs?
- Are there external systems that interact with ours?
- Who are the administrators/operators?

**Example (Uber):**
```
Users:
├── Riders (request rides, track driver, pay)
├── Drivers (accept rides, navigate, receive payment)
├── Admins (manage users, handle disputes, analytics)
└── External Systems (payment gateways, maps API)
```

### 2. Define Core Features (MVP)

**Questions to Ask:**
- What is the minimum set of features for the system to be useful?
- What are the must-have vs nice-to-have features?
- What is explicitly out of scope?

**Prioritization Framework:**
```
Priority 1 (P0) - Must Have:
  - Core functionality without which product doesn't work
  - Example: For Twitter - posting tweets, viewing timeline

Priority 2 (P1) - Should Have:
  - Important features that enhance core experience
  - Example: For Twitter - likes, retweets, replies

Priority 3 (P2) - Nice to Have:
  - Features that can be added later
  - Example: For Twitter - analytics, scheduling
```

### 3. Map User Journeys

For each user type, map their primary workflows:

**Template:**
```
User Journey: [Name]
Actor: [User Type]
Precondition: [What must be true before]
Steps:
  1. User does X
  2. System responds with Y
  3. User does Z
Postcondition: [What is true after]
```

**Example (E-commerce Checkout):**
```
User Journey: Complete Purchase
Actor: Registered Customer
Precondition: User has items in cart, is logged in

Steps:
  1. User clicks "Checkout"
  2. System displays cart summary and shipping options
  3. User selects shipping method
  4. System displays payment options
  5. User enters payment details
  6. System validates payment with payment gateway
  7. System confirms order and sends confirmation email
  8. User sees order confirmation page

Postcondition: Order is created, inventory updated, payment captured
```

### 4. Identify Data Requirements

**Questions to Ask:**
- What data does each feature need to read?
- What data does each feature create or modify?
- What are the relationships between data entities?
- What data needs to be persisted vs computed?

---

## Functional Requirements Checklist

### Core Operations (CRUD)
- [ ] Create: What entities can be created?
- [ ] Read: What data can be queried? What filters/sorting?
- [ ] Update: What can be modified? Who can modify?
- [ ] Delete: Soft delete or hard delete? Cascading deletes?

### User Management
- [ ] Registration and onboarding
- [ ] Authentication (login, logout, sessions)
- [ ] Profile management
- [ ] Role-based permissions
- [ ] Account recovery/password reset

### Content/Data Management
- [ ] What content types exist?
- [ ] Who can create/edit/delete content?
- [ ] Content moderation requirements
- [ ] Version history/audit trail

### Search and Discovery
- [ ] Full-text search requirements
- [ ] Filtering and faceting
- [ ] Sorting options
- [ ] Pagination approach

### Notifications
- [ ] What events trigger notifications?
- [ ] What channels? (email, push, SMS, in-app)
- [ ] Real-time vs batched?
- [ ] User preferences and opt-out

### Integrations
- [ ] Third-party APIs to consume
- [ ] APIs to expose
- [ ] Webhooks to send/receive
- [ ] Import/export functionality

---

## Common Patterns by System Type

### Social Media Platform
```
Core Features:
├── Post Creation (text, images, video)
├── Timeline/Feed (personalized, chronological)
├── Social Graph (follow, friend, block)
├── Engagement (like, comment, share)
├── Direct Messaging
├── Notifications
└── Search (users, content, hashtags)
```

### E-commerce Platform
```
Core Features:
├── Product Catalog (browse, search, filter)
├── Shopping Cart (add, update, remove)
├── Checkout (shipping, payment)
├── Order Management (track, cancel, return)
├── User Accounts (profile, addresses, payment methods)
├── Reviews and Ratings
└── Inventory Management
```

### Messaging/Chat System
```
Core Features:
├── 1:1 Messaging (send, receive, read receipts)
├── Group Chats (create, manage, leave)
├── Media Sharing (images, files, voice)
├── Presence (online, typing indicators)
├── Push Notifications
├── Message Search
└── End-to-end Encryption
```

### Ride-Sharing Platform
```
Core Features:
├── Ride Request (pickup, dropoff, ride type)
├── Driver Matching (location-based, availability)
├── Real-time Tracking (driver location, ETA)
├── Trip Management (start, end, cancel)
├── Payments (fare calculation, processing)
├── Ratings and Reviews
└── Trip History
```

---

## Interview Tips

### Questions to Ask the Interviewer
1. "Who are the main users of this system?"
2. "What is the most critical user flow?"
3. "What features are out of scope for this discussion?"
4. "Should we focus on any specific aspect?"
5. "Are there any unique constraints I should know about?"

### Scoping the Problem
- Don't try to design everything - focus on core flows
- Explicitly state assumptions
- Get agreement on scope before designing
- Prioritize depth over breadth

### Common Mistakes to Avoid
- Jumping into technical design too quickly
- Not clarifying scope with the interviewer
- Trying to include every possible feature
- Ignoring edge cases and error scenarios
- Not considering different user types

---

## Template: Functional Requirements Document

```markdown
# System: [Name]

## 1. Overview
Brief description of what the system does.

## 2. Users/Actors
| Actor | Description | Key Actions |
|-------|-------------|-------------|
| User Type 1 | Description | Action 1, Action 2 |
| User Type 2 | Description | Action 1, Action 2 |

## 3. Core Features (P0)
### Feature 1: [Name]
- Description: What it does
- Inputs: What data is needed
- Outputs: What is produced
- Business Rules: Constraints and logic

### Feature 2: [Name]
...

## 4. Secondary Features (P1)
...

## 5. Out of Scope
- Feature X: Reason
- Feature Y: Reason

## 6. Assumptions
- Assumption 1
- Assumption 2
```

---

## Next Steps

After gathering functional requirements:
1. → [Non-Functional Requirements](non-functional-requirements.md) - Define quality attributes
2. → [Estimation](../02-estimation/) - Calculate scale requirements
3. → [API Design](../03-api-design/) - Design the interface
