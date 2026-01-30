# Question Bank

Questions to ask at each stage of the system design interview.

---

## Phase 1: Requirements Questions

### User & Scope

```
Who:
  □ "Who are the primary users of this system?"
  □ "Are there different user types with different needs?"
  □ "Are there admin/internal users to consider?"

What:
  □ "What are the most critical features to focus on?"
  □ "What features are explicitly out of scope?"
  □ "Should we focus on any specific user flow?"

Why:
  □ "What's the main problem we're solving?"
  □ "What's the business impact of this system?"
```

### Scale & Performance

```
Scale:
  □ "How many daily active users are expected?"
  □ "What's the expected growth rate?"
  □ "Are there seasonal or event-driven spikes?"

Performance:
  □ "What latency is acceptable for the main operations?"
  □ "Is real-time response required, or can some things be async?"
  □ "What's the expected read vs write ratio?"
```

### Consistency & Availability

```
Consistency:
  □ "Is eventual consistency acceptable, or do we need strong consistency?"
  □ "How stale can the data be?"
  □ "Are there operations that absolutely require consistency?"

Availability:
  □ "What's the availability target? (99.9%, 99.99%)"
  □ "What's the acceptable planned maintenance window?"
  □ "Is this a global service requiring multi-region?"
```

### Constraints

```
Technical:
  □ "Are there existing systems we need to integrate with?"
  □ "Are there technology constraints or preferences?"
  □ "What's the team's expertise?"

Business:
  □ "Are there budget constraints?"
  □ "Are there compliance requirements? (GDPR, HIPAA)"
  □ "What's the timeline?"
```

---

## Phase 2: Estimation Questions

### Traffic

```
□ "How many users are expected to use this feature daily?"
□ "How many times per day will a typical user perform this action?"
□ "What's the peak to average traffic ratio?"
```

### Data

```
□ "How much data does each user/action generate?"
□ "How long do we need to retain data?"
□ "Is there media (images, video) to consider?"
```

### Growth

```
□ "What's the expected user growth?"
□ "Are there any upcoming events that could spike traffic?"
□ "Should we design for 10x the current scale?"
```

---

## Phase 3: API Questions

```
□ "Should we support multiple client types? (web, mobile, third-party)"
□ "Is this a public API or internal only?"
□ "Are there existing API patterns we should follow?"
□ "What authentication method is preferred?"
```

---

## Phase 4: High-Level Design Questions

### Architecture

```
□ "Is this a greenfield project or extending existing system?"
□ "Are microservices preferred over monolith?"
□ "Is there an existing infrastructure (cloud, on-prem)?"
```

### Data Flow

```
□ "What are the most critical user journeys to handle?"
□ "Are there any real-time requirements?"
□ "What happens if a component fails?"
```

---

## Phase 5: Deep Dive Questions

### Database

```
□ "What are the most common query patterns?"
□ "How much historical data do we need to query?"
□ "Are there complex relationships between entities?"
□ "Do we need full-text search capabilities?"
```

### Caching

```
□ "What data is read frequently?"
□ "How often does the data change?"
□ "Is stale data acceptable? For how long?"
```

### Messaging

```
□ "Are there operations that can be processed asynchronously?"
□ "What's the tolerance for message delivery delay?"
□ "Do we need exactly-once processing?"
```

### Scaling

```
□ "What's the most likely bottleneck?"
□ "How do we handle sudden traffic spikes?"
□ "What happens during database maintenance?"
```

---

## Questions to Self-Check

### During Design

```
□ "How does this handle 10x the traffic?"
□ "What happens when this component fails?"
□ "Where are the single points of failure?"
□ "What are the trade-offs of this decision?"
□ "Is there a simpler approach that would work?"
```

### Before Moving On

```
□ "Does this address the main requirements?"
□ "Have I explained the data flow clearly?"
□ "Are there any obvious bottlenecks?"
□ "Should I go deeper on any area?"
```

---

## Questions by System Type

### Social Media / Content Platform

```
□ "Should the feed be real-time or eventually consistent?"
□ "How do we handle viral content (celebrity with millions of followers)?"
□ "What's the content moderation requirement?"
□ "Should we support offline access?"
```

### E-Commerce

```
□ "How do we handle inventory during high-demand sales?"
□ "What happens if payment succeeds but order fails?"
□ "Do we need to support multiple currencies/regions?"
□ "What's the return/refund process?"
```

### Messaging / Chat

```
□ "Do we need end-to-end encryption?"
□ "How do we handle offline message delivery?"
□ "Is read receipt/typing indicator needed?"
□ "What's the message retention policy?"
```

### Search

```
□ "What's the expected index size?"
□ "How quickly do changes need to be searchable?"
□ "Is fuzzy/typo-tolerant search needed?"
□ "Do we need personalized results?"
```

### Video / Streaming

```
□ "What video qualities do we need to support?"
□ "Is live streaming required or just on-demand?"
□ "What's the geographic distribution of users?"
□ "Is DRM/content protection needed?"
```

### Location-Based

```
□ "How precise does location need to be?"
□ "How frequently do locations update?"
□ "Is real-time tracking required?"
□ "What happens in areas with poor connectivity?"
```

---

## Questions That Show Seniority

### Operational Thinking

```
□ "How would we deploy updates without downtime?"
□ "What monitoring would we set up?"
□ "How would we debug issues in production?"
□ "What's the incident response process?"
```

### Business Thinking

```
□ "How does this tie to business metrics?"
□ "What would we A/B test first?"
□ "What's the cost model for this design?"
□ "How does this impact other teams?"
```

### Long-term Thinking

```
□ "How would this evolve as we grow?"
□ "What technical debt would this create?"
□ "What would we do differently in v2?"
□ "How does this fit into the broader architecture?"
```

---

## Red Flags to Avoid

### Questions NOT to Ask

```
✗ "Should I use React or Vue?"
   (Too low-level for system design)

✗ "What language should I use?"
   (Usually not relevant)

✗ "Is my design correct?"
   (There's no single correct answer)

✗ Questions you should know the answer to
   (Shows lack of preparation)
```

### When to Stop Asking

```
Move on when:
  - You have enough to start designing
  - Interviewer signals to proceed
  - You're spending too much time clarifying

Don't:
  - Ask questions just to fill time
  - Repeat questions you've already asked
  - Argue with the interviewer's constraints
```

---

## Next Steps

1. → [Interview Framework](interview-framework.md) - Overall structure
2. → [Evaluation Criteria](evaluation-criteria.md) - How you're judged
3. → [Case Studies](../10-case-studies/) - Apply these questions
