# Data & Feature Engineering

Deep dive into data pipelines, labeling strategies, and feature stores for ML systems.

---

## Data Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATA PIPELINE                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │   Sources   │───>│  Ingestion  │───>│  Processing │                 │
│  │             │    │             │    │             │                 │
│  │ - Databases │    │ - Batch     │    │ - Clean     │                 │
│  │ - Events    │    │ - Stream    │    │ - Transform │                 │
│  │ - Logs      │    │ - CDC       │    │ - Aggregate │                 │
│  │ - External  │    │             │    │             │                 │
│  └─────────────┘    └─────────────┘    └──────┬──────┘                 │
│                                               │                         │
│                         ┌─────────────────────┴─────────────────────┐  │
│                         │                                           │  │
│                         ▼                                           ▼  │
│                  ┌─────────────┐                           ┌───────────┐│
│                  │  Data Lake  │                           │  Feature  ││
│                  │  (Raw)      │                           │   Store   ││
│                  └──────┬──────┘                           └───────────┘│
│                         │                                               │
│                         ▼                                               │
│                  ┌─────────────┐                                        │
│                  │   Data      │                                        │
│                  │  Warehouse  │                                        │
│                  │ (Processed) │                                        │
│                  └─────────────┘                                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Acquisition

### Data Sources

```
First-Party Data:
  - User interactions (clicks, views, purchases)
  - Application logs
  - Transactions
  - User-generated content

Second-Party Data:
  - Partner data sharing
  - API integrations

Third-Party Data:
  - Purchased datasets
  - Public datasets
  - Enrichment services
```

### Batch vs Streaming

```
Batch Ingestion:
  - Scheduled (daily, hourly)
  - Large volumes
  - Tools: Spark, Airflow
  - Use: Historical data, training

  Example pipeline:
    Airflow DAG → Extract from DB → Transform → Load to Data Lake

Streaming Ingestion:
  - Real-time/near-real-time
  - Continuous flow
  - Tools: Kafka, Flink, Kinesis
  - Use: Real-time features, events

  Example pipeline:
    Events → Kafka → Flink → Feature Store
```

### Change Data Capture (CDC)

```
Capture changes from databases in real-time.

┌──────────┐    ┌─────────────┐    ┌─────────────┐
│ Database │───>│   Debezium  │───>│    Kafka    │
│ (MySQL)  │    │   (CDC)     │    │             │
└──────────┘    └─────────────┘    └──────┬──────┘
                                          │
                         ┌────────────────┴────────────────┐
                         │                                 │
                         ▼                                 ▼
                  ┌─────────────┐                  ┌─────────────┐
                  │   Feature   │                  │  Analytics  │
                  │    Store    │                  │   (Spark)   │
                  └─────────────┘                  └─────────────┘

Benefits:
  - Real-time data sync
  - No impact on source DB
  - Complete change history
```

---

## Data Labeling

### Labeling Strategies

```
1. Manual Labeling:
   - Human annotators
   - High quality, expensive
   - Use: Training data, edge cases

   Platforms: Labelbox, Scale AI, Amazon MTurk

2. Semi-Supervised:
   - Small labeled set + large unlabeled
   - Model labels similar examples
   - Human reviews uncertain cases

3. Weak Supervision:
   - Programmatic labeling functions
   - Combine multiple noisy signals
   - Tools: Snorkel

   Example:
     def label_spam(email):
         if "buy now" in email.lower():
             return SPAM
         elif email.sender in whitelist:
             return NOT_SPAM
         return ABSTAIN

4. Self-Training:
   - Train on labeled data
   - Predict unlabeled data
   - Add high-confidence predictions to training

5. Active Learning:
   - Model requests labels for uncertain examples
   - Maximizes information per label
   - Reduces labeling cost
```

### Label Quality

```
Quality Measures:
  - Inter-annotator agreement
  - Label accuracy (vs gold standard)
  - Coverage (% labeled)

Improving Quality:
  - Clear labeling guidelines
  - Multiple annotators per example
  - Regular calibration sessions
  - Automated quality checks

Handling Noise:
  - Confident learning (identify mislabeled)
  - Label smoothing
  - Noise-robust loss functions
```

---

## Feature Engineering

### Feature Types

```
Numerical Features:
  - Age, price, count
  - Transformations: log, sqrt, binning
  - Normalization: min-max, z-score

Categorical Features:
  - Country, category, brand
  - Encoding: one-hot, target, embedding
  - High cardinality: hashing, embeddings

Text Features:
  - TF-IDF, word embeddings
  - Sentence transformers
  - N-grams

Time-Based Features:
  - Day of week, hour, month
  - Time since last event
  - Cyclical encoding (sin/cos)

Aggregation Features:
  - Count, sum, mean, max over window
  - Rolling statistics
  - User/item level aggregates
```

### Feature Engineering Patterns

```
1. Interaction Features:
   price_per_unit = price / quantity
   ctr = clicks / impressions

2. Lag Features:
   purchases_last_7_days
   avg_session_duration_last_30_days

3. Window Aggregations:
   sum_purchases_7d, sum_purchases_30d, sum_purchases_90d
   → ratio_7d_30d = sum_7d / sum_30d

4. Cross Features:
   user_category_affinity = user × category
   device_time_of_day = device × hour

5. Embedding Features:
   user_embedding (learned from interactions)
   item_embedding (from content/behavior)
```

---

## Feature Store

### Why Feature Store?

```
Problems without Feature Store:
  ✗ Training-serving skew (different code paths)
  ✗ Duplicate feature computation
  ✗ No feature reuse across teams
  ✗ Inconsistent feature definitions
  ✗ Hard to manage feature versions

Feature Store Benefits:
  ✓ Single source of truth for features
  ✓ Consistent features for training and serving
  ✓ Feature reuse and discovery
  ✓ Versioning and lineage
  ✓ Low-latency online serving
```

### Feature Store Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        FEATURE STORE                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Feature Registry                              │   │
│  │  - Feature definitions and metadata                             │   │
│  │  - Versioning and lineage                                       │   │
│  │  - Discovery and documentation                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────┐    ┌──────────────────────────┐          │
│  │     Offline Store        │    │      Online Store        │          │
│  │                          │    │                          │          │
│  │  - Historical features   │    │  - Latest features       │          │
│  │  - Training data         │    │  - Low-latency serving   │          │
│  │  - Batch processing      │    │  - Real-time inference   │          │
│  │                          │    │                          │          │
│  │  Storage: S3, GCS,       │    │  Storage: Redis,         │          │
│  │           Data Lake      │    │           DynamoDB       │          │
│  └──────────────────────────┘    └──────────────────────────┘          │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              Feature Transformation Engine                       │   │
│  │  - Batch: Spark, Flink                                          │   │
│  │  - Streaming: Kafka Streams, Flink                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Online vs Offline Features

```
Offline Features (Batch):
  - Computed periodically (hourly, daily)
  - Historical aggregations
  - Training data generation

  Examples:
    user_total_purchases_lifetime
    item_avg_rating
    user_category_preferences

Online Features (Real-time):
  - Computed at request time or near-real-time
  - Current context
  - Low-latency requirement

  Examples:
    user_last_click_category
    session_duration
    current_cart_value
```

### Feature Store Solutions

```
Platform         │ Type         │ Best For
─────────────────┼──────────────┼──────────────────────
Feast            │ Open source  │ Flexibility, K8s
Tecton           │ Managed      │ Real-time features
Databricks FS    │ Managed      │ Databricks users
SageMaker FS     │ Managed      │ AWS ecosystem
Vertex AI FS     │ Managed      │ GCP ecosystem
Hopsworks        │ Managed/OSS  │ Full MLOps platform
```

---

## Data Quality

### Data Quality Dimensions

```
Completeness:  Are all required fields present?
Accuracy:      Is the data correct?
Consistency:   Is data consistent across sources?
Timeliness:    Is data fresh enough?
Validity:      Does data conform to expected format?
Uniqueness:    Are there duplicates?
```

### Data Validation

```
Schema Validation:
  - Column types
  - Required fields
  - Value ranges

Statistical Validation:
  - Distribution checks
  - Outlier detection
  - Missing value rates

Cross-Dataset Validation:
  - Referential integrity
  - Consistency across sources

Tools:
  - Great Expectations
  - Deequ
  - TensorFlow Data Validation
```

### Handling Data Issues

```
Missing Values:
  - Imputation (mean, median, mode)
  - Indicator variable
  - Model-based imputation

Outliers:
  - Winsorization (cap at percentile)
  - Remove if data error
  - Robust scaling

Class Imbalance:
  - Oversampling (SMOTE)
  - Undersampling
  - Class weights
  - Threshold adjustment
```

---

## Interview Tips

### Questions to Ask

```
1. What data sources are available?
   → Determines feature possibilities

2. How is ground truth collected?
   → Labeling strategy

3. How fresh does data need to be?
   → Batch vs streaming

4. What's the data volume?
   → Infrastructure needs

5. Are there privacy constraints?
   → Feature engineering limitations
```

### Key Points to Discuss

```
✓ Data pipeline architecture
✓ Feature engineering approach
✓ Training-serving consistency
✓ Data quality monitoring
✓ Privacy and compliance
```

---

## Next Steps

1. → [Model Training](model-training.md) - Training infrastructure
2. → [Model Serving](model-serving.md) - Inference at scale
3. → [ML Monitoring](ml-monitoring.md) - Monitoring data and models
