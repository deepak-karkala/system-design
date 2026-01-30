# ML System Design Overview

Comprehensive guide to designing production machine learning systems.

---

## ML System vs Traditional System Design

```
Traditional System Design:
  - Deterministic behavior
  - Clear input → output mapping
  - Logic is coded explicitly

ML System Design:
  - Probabilistic behavior
  - Behavior learned from data
  - Logic emerges from training

Additional Concerns:
  - Data quality and management
  - Model training infrastructure
  - Feature engineering pipeline
  - Model serving and inference
  - Monitoring for data/model drift
  - Experiment tracking and versioning
```

---

## ML System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ML SYSTEM ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │    Data     │───>│   Feature   │───>│   Model     │                 │
│  │  Ingestion  │    │   Store     │    │  Training   │                 │
│  └─────────────┘    └─────────────┘    └──────┬──────┘                 │
│         │                 │                   │                         │
│         │                 │            ┌──────▼──────┐                  │
│         │                 │            │   Model     │                  │
│         │                 │            │  Registry   │                  │
│         │                 │            └──────┬──────┘                  │
│         │                 │                   │                         │
│         │           ┌─────▼─────┐      ┌──────▼──────┐                  │
│         │           │  Online   │      │   Model     │                  │
│         └──────────>│  Feature  │<─────│  Serving    │<── Requests     │
│                     │   Store   │      └─────────────┘                  │
│                     └───────────┘             │                         │
│                                               │                         │
│                                        ┌──────▼──────┐                  │
│                                        │ Monitoring  │                  │
│                                        │ & Feedback  │                  │
│                                        └─────────────┘                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ML Interview Framework

### Phase 1: Problem Definition (5 min)

```
1. Clarify the ML objective:
   - What problem are we solving?
   - Is ML the right solution?
   - What's the business impact?

2. Define success metrics:
   - Business metrics (revenue, engagement)
   - ML metrics (accuracy, precision, recall)
   - How do they relate?

3. Identify constraints:
   - Latency requirements
   - Scale (predictions/second)
   - Data availability
   - Privacy considerations
```

### Phase 2: Data (10 min)

```
1. Data sources:
   - What data is available?
   - How is it collected?
   - What's the volume and velocity?

2. Data quality:
   - Missing values
   - Label noise
   - Class imbalance
   - Data freshness

3. Feature engineering:
   - What features are useful?
   - How to compute them?
   - Online vs offline features
```

### Phase 3: Model (10 min)

```
1. Model selection:
   - Simple baseline first
   - Complexity vs performance
   - Interpretability needs

2. Training:
   - Training data pipeline
   - Distributed training needs
   - Hyperparameter tuning

3. Evaluation:
   - Offline metrics
   - Online metrics
   - A/B testing strategy
```

### Phase 4: Serving (10 min)

```
1. Inference mode:
   - Real-time vs batch
   - Latency requirements
   - Throughput needs

2. Infrastructure:
   - Model serving platform
   - Scaling strategy
   - Caching considerations

3. Deployment:
   - Canary/shadow deployment
   - Rollback strategy
   - Feature flag integration
```

### Phase 5: Monitoring (5 min)

```
1. Model monitoring:
   - Prediction distribution
   - Feature drift
   - Model performance decay

2. Data monitoring:
   - Input data quality
   - Missing features
   - Data pipeline health

3. Feedback loop:
   - Collecting labels
   - Retraining triggers
   - Continuous improvement
```

---

## Common ML System Types

### Recommendation Systems

```
Use Cases:
  - Product recommendations (Amazon)
  - Content recommendations (Netflix, YouTube)
  - People you may know (LinkedIn)

Architecture:
  ┌──────────────────────────────────────────────────────────┐
  │                 Recommendation System                     │
  ├──────────────────────────────────────────────────────────┤
  │                                                           │
  │  Candidate Generation          Ranking                   │
  │  ├── Collaborative filtering   ├── Learning to rank     │
  │  ├── Content-based            ├── Deep learning        │
  │  └── Two-tower models         └── Feature crossing     │
  │                                                           │
  │  ┌──────────────┐    ┌──────────────┐    ┌───────────┐  │
  │  │  Candidates  │───>│   Ranking    │───>│  Results  │  │
  │  │  (1000s)     │    │   Model      │    │   (10s)   │  │
  │  └──────────────┘    └──────────────┘    └───────────┘  │
  │                                                           │
  └──────────────────────────────────────────────────────────┘
```

### Search Systems

```
Use Cases:
  - Web search (Google)
  - E-commerce search
  - Enterprise search

Architecture:
  Query → Query Understanding → Retrieval → Ranking → Results
           ├── Spell correction
           ├── Query expansion
           └── Intent classification

Ranking signals:
  - Relevance (BM25, semantic similarity)
  - Popularity (click-through rate)
  - Personalization
  - Freshness
```

### Fraud Detection

```
Use Cases:
  - Payment fraud
  - Account takeover
  - Fake content/reviews

Challenges:
  - Extreme class imbalance
  - Adversarial actors
  - Real-time requirements
  - Explainability needs

Architecture:
  Transaction → Feature Extraction → Model → Decision
                                       │
                    ┌──────────────────┘
                    │
         ┌─────────▼─────────┐
         │  Rules Engine     │
         │  (hard rules +    │
         │   ML scores)      │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  Review Queue     │
         │  (human-in-loop)  │
         └───────────────────┘
```

### Ads/Click Prediction

```
Use Cases:
  - Display ads (Google, Facebook)
  - Sponsored content
  - Email targeting

Key Metrics:
  - CTR (Click-Through Rate)
  - Conversion rate
  - Revenue per impression

Architecture:
  Ad Request → Candidate Selection → CTR Prediction → Auction → Ad Served
                                            │
                    ┌───────────────────────┘
                    │
         Features:
         ├── User features (history, demographics)
         ├── Ad features (creative, category)
         ├── Context features (time, device, page)
         └── Cross features (user × ad interactions)
```

---

## Key Decisions

### When to Use ML

```
Use ML when:
  ✓ Pattern is complex/hard to code
  ✓ Pattern changes over time
  ✓ Scale makes manual review impossible
  ✓ Sufficient data is available
  ✓ Cost of errors is manageable

Don't use ML when:
  ✗ Simple rules suffice
  ✗ Interpretability is critical and model is not
  ✗ Insufficient data
  ✗ Problem requires 100% accuracy
  ✗ Faster/cheaper alternatives exist
```

### Real-time vs Batch

```
Real-time Inference:
  - User-facing features
  - Latency: < 100ms
  - Example: Search ranking, fraud detection

  Challenges:
    - Feature computation at request time
    - Model serving infrastructure
    - Caching strategies

Batch Inference:
  - Pre-computed predictions
  - Latency: minutes to hours
  - Example: Email campaigns, recommendations

  Challenges:
    - Freshness of predictions
    - Storage of pre-computed results
    - Staleness handling
```

### Model Complexity vs Performance

```
Start simple, add complexity when needed:

Level 1: Rules-based
  - Interpretable
  - Fast to implement
  - No data needed

Level 2: Linear models (Logistic Regression)
  - Interpretable
  - Fast training and inference
  - Good baseline

Level 3: Tree-based (XGBoost, LightGBM)
  - Handles non-linear relationships
  - Feature importance
  - Good for tabular data

Level 4: Deep Learning
  - Complex patterns
  - Requires more data
  - Embeddings for categorical/text

Level 5: Large Language Models
  - Zero/few-shot learning
  - Expensive inference
  - Best for text/language tasks
```

---

## Interview Tips

### Questions to Ask

```
1. What's the business objective?
   → Defines success metrics

2. What data is available?
   → Determines feature possibilities

3. What's the latency requirement?
   → Real-time vs batch decision

4. How often does the pattern change?
   → Retraining frequency

5. What's the cost of errors?
   → Precision vs recall trade-off
```

### Common Mistakes

```
✗ Jumping to deep learning immediately
✗ Ignoring data quality issues
✗ Not defining clear metrics
✗ Forgetting about serving latency
✗ Ignoring monitoring and feedback
```

### Key Points to Demonstrate

```
✓ Problem formulation as ML task
✓ Data pipeline design
✓ Feature engineering thinking
✓ Model selection rationale
✓ Serving architecture
✓ Monitoring and iteration
```

---

## Next Steps

1. → [Data & Features](data-and-features.md) - Feature engineering deep dive
2. → [Model Training](model-training.md) - Training infrastructure
3. → [Model Serving](model-serving.md) - Inference at scale
4. → [ML Monitoring](ml-monitoring.md) - Monitoring ML systems
