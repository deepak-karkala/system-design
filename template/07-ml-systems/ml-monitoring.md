# ML Monitoring & Observability

Monitoring ML systems for data drift, model degradation, and operational health.

---

## Why ML Monitoring is Different

```
Traditional Software:
  - Deterministic behavior
  - Bugs are reproducible
  - Errors are explicit

ML Systems:
  - Probabilistic behavior
  - Silent failures (wrong but valid output)
  - Performance degrades gradually
  - Depends on data distribution

New Failure Modes:
  - Data drift (input distribution changes)
  - Concept drift (relationship changes)
  - Model staleness
  - Feature pipeline failures
```

---

## Monitoring Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      ML MONITORING STACK                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Layer 4: Business Metrics                                              │
│  ├── Revenue impact                                                      │
│  ├── User engagement                                                     │
│  └── Conversion rates                                                    │
│                                                                          │
│  Layer 3: Model Performance                                              │
│  ├── Prediction accuracy                                                 │
│  ├── Precision, recall, F1                                              │
│  └── Online A/B test results                                            │
│                                                                          │
│  Layer 2: Data Quality                                                   │
│  ├── Feature drift                                                       │
│  ├── Label drift                                                         │
│  └── Data quality checks                                                │
│                                                                          │
│  Layer 1: Infrastructure                                                 │
│  ├── Latency, throughput                                                │
│  ├── Error rates                                                        │
│  └── Resource utilization                                               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Monitoring

### Feature Drift Detection

```
Feature drift: Input data distribution changes from training.

Detection Methods:

1. Statistical Tests:
   - KS Test (Kolmogorov-Smirnov)
   - Chi-Square Test (categorical)
   - PSI (Population Stability Index)

   PSI Interpretation:
     < 0.1:  No significant change
     0.1-0.2: Moderate change
     > 0.2:  Significant change

2. Distribution Comparison:
   Training:   [0.1, 0.2, 0.3, 0.25, 0.15]
   Production: [0.05, 0.1, 0.4, 0.3, 0.15]
   → Shift detected in middle bins

3. Summary Statistics:
   Track: mean, std, min, max, nulls, cardinality
   Alert when outside expected range
```

### Data Quality Monitoring

```
Checks to implement:

Schema Checks:
  □ Expected columns present
  □ Column types correct
  □ No unexpected null values

Value Checks:
  □ Values in expected range
  □ Categorical values in expected set
  □ No negative values (where applicable)

Volume Checks:
  □ Expected data volume
  □ No missing time periods
  □ Reasonable record count

Freshness Checks:
  □ Data arrived on time
  □ Latest timestamp recent
  □ No stale data
```

### Label Drift

```
Label drift: Target distribution changes.

Example:
  Training: 5% fraud rate
  Production: 15% fraud rate
  → Model may be miscalibrated

Detection:
  - Monitor prediction distribution
  - Compare to historical labels (if available)
  - Track class balance over time

Causes:
  - Seasonal patterns
  - External events
  - User behavior change
  - Data collection change
```

---

## Model Monitoring

### Online Performance Metrics

```
Classification:
  - Accuracy (overall correctness)
  - Precision (of positives, how many correct)
  - Recall (of actual positives, how many found)
  - F1 Score (harmonic mean)
  - AUC-ROC (ranking quality)

Regression:
  - MAE (Mean Absolute Error)
  - MSE/RMSE (Mean Squared Error)
  - MAPE (Mean Absolute Percentage Error)

Ranking:
  - NDCG (Normalized Discounted Cumulative Gain)
  - MRR (Mean Reciprocal Rank)
  - MAP (Mean Average Precision)
```

### Delayed Labels Problem

```
Challenge: Ground truth isn't immediately available.

Examples:
  - Fraud: Know result after investigation (days)
  - Recommendations: Know if user purchased (hours/days)
  - Ads: Know conversion after 30 days

Solutions:

1. Proxy Metrics:
   Use correlated immediate signals
   - Click as proxy for purchase
   - Session length as proxy for satisfaction

2. Partial Labels:
   Use available subset of labels
   - Sample with known outcomes
   - Subset with faster feedback

3. Prediction Monitoring:
   Even without labels, monitor:
   - Prediction distribution shift
   - Confidence score distribution
   - Unusual prediction patterns
```

### Model Staleness

```
Model performance degrades over time due to:
  - Data drift
  - Concept drift
  - Seasonal patterns
  - External events

Monitoring:
  Time ──────────────────────────────────────>

  Accuracy
    │  ┌──────┐
    │  │      └────────┐
    │  │               └──────┐
    │  │                      └─── Alert threshold
    └──┴─────────────────────────────────────

Retraining Triggers:
  - Scheduled (daily, weekly)
  - Performance threshold breached
  - Data drift detected
  - Significant new data available
```

---

## Alerting Strategy

### Alert Design

```
Good ML alerts:
  ✓ Actionable
  ✓ Based on business impact
  ✓ Include context (what changed)
  ✓ Appropriate severity

Alert Levels:
  P1: Model completely failed, immediate action
      - Serving errors > 50%
      - Complete prediction failure

  P2: Significant degradation
      - Accuracy dropped > 10%
      - Major data quality issue

  P3: Notable change, investigate
      - Feature drift detected
      - Prediction distribution shift

  P4: Informational
      - Minor drift
      - Retraining completed
```

### Alert Thresholds

```
Static Thresholds:
  Alert if: accuracy < 0.85

Dynamic Thresholds:
  Alert if: metric deviates > 2 std from rolling mean

Compound Alerts:
  Alert if: drift_score > 0.2 AND accuracy_drop > 5%

Example configuration:
  alerts:
    - name: model_accuracy_drop
      condition: accuracy < 0.85
      severity: P2
      runbook: link_to_runbook

    - name: feature_drift
      condition: psi > 0.2
      severity: P3
      runbook: link_to_runbook
```

---

## Monitoring Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ML MONITORING ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │   Model     │───>│  Metrics    │───>│  Time-Series│                 │
│  │  Serving    │    │  Collector  │    │   Database  │                 │
│  └─────────────┘    └─────────────┘    └──────┬──────┘                 │
│         │                                     │                         │
│         │                                     │                         │
│         ▼                                     ▼                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │  Prediction │    │   Drift     │    │ Dashboards  │                 │
│  │    Logs     │───>│  Detection  │    │  & Alerts   │                 │
│  └─────────────┘    └─────────────┘    └─────────────┘                 │
│                            │                                            │
│                            ▼                                            │
│                     ┌─────────────┐                                     │
│                     │  Retraining │                                     │
│                     │   Trigger   │                                     │
│                     └─────────────┘                                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Tools:
  Metrics: Prometheus, CloudWatch
  Drift: Evidently, WhyLabs, Arize
  Dashboards: Grafana, custom
  Logging: ELK, Datadog
```

---

## Logging for ML

### What to Log

```
Prediction Logs:
{
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req-123",
  "model_version": "v1.2.3",
  "features": {
    "user_id": "user-456",
    "item_id": "item-789",
    "user_age": 25,
    "item_category": "electronics"
  },
  "prediction": 0.85,
  "confidence": 0.92,
  "latency_ms": 15,
  "model_name": "recommendation-model"
}

What to include:
  ✓ All input features
  ✓ Model prediction
  ✓ Model version
  ✓ Timestamp
  ✓ Request ID (for tracing)
  ✓ Latency

Privacy considerations:
  - Anonymize PII
  - Aggregate where possible
  - Follow data retention policies
```

### Sampling Strategy

```
Full logging expensive at scale.
Sampling strategies:

1. Random Sampling:
   Log 10% of predictions
   Pro: Simple
   Con: May miss rare cases

2. Stratified Sampling:
   Ensure representation of all segments
   Pro: Better coverage
   Con: More complex

3. Importance Sampling:
   Log more for uncertain predictions
   Pro: Captures interesting cases
   Con: Biased sample

4. Trigger-based:
   Log all when metrics anomaly
   Pro: Captures issues
   Con: May miss slow drift
```

---

## A/B Testing for ML

### Experiment Design

```
Control: Current model (baseline)
Treatment: New model (challenger)

Requirements:
  - Random user assignment
  - Consistent assignment (same user, same bucket)
  - Sufficient sample size
  - Statistical significance

Metrics:
  Primary: Business metric (conversion, revenue)
  Secondary: ML metrics (accuracy, latency)
  Guardrails: Safety metrics (errors, complaints)
```

### Analysis

```
Statistical significance:
  - P-value < 0.05 (typically)
  - Confidence intervals
  - Minimum detectable effect

Watch for:
  - Novelty effects (new model looks better initially)
  - Simpson's paradox (segment-level differences)
  - Multiple testing (Bonferroni correction)

Decision framework:
  If treatment significantly better: Roll out
  If treatment significantly worse: Revert
  If no significant difference: Consider cost/complexity
```

---

## Incident Response

### Runbook Template

```
Incident: Model Performance Degradation

Detection:
  - Alert: model_accuracy_drop triggered
  - Dashboard shows accuracy < threshold

Diagnosis:
  1. Check recent model deployments
  2. Check feature pipeline health
  3. Check data quality metrics
  4. Compare prediction distributions

Mitigation:
  1. If recent deployment: Rollback
     kubectl rollout undo deployment/model-server

  2. If data issue: Fix pipeline, backfill

  3. If drift: Trigger retraining
     trigger_retraining(model_id="abc", reason="drift")

  4. If no quick fix: Fallback to simpler model
     set_feature_flag("use_fallback_model", true)

Escalation:
  - P1: Page ML on-call immediately
  - P2: Slack alert, 1-hour response
  - P3: Next business day
```

---

## Interview Tips

### Questions to Ask

```
1. How is ground truth collected?
   → Delayed label strategy

2. What's the acceptable accuracy drop?
   → Alert thresholds

3. How often can we retrain?
   → Monitoring frequency

4. What's the business impact of wrong predictions?
   → Prioritization of metrics

5. Are there regulatory requirements?
   → Audit and explainability needs
```

### Key Points to Discuss

```
✓ Data drift detection approach
✓ Delayed label handling
✓ Online vs offline metrics
✓ Alerting strategy
✓ Retraining triggers
✓ A/B testing methodology
```

---

## Next Steps

1. → [MLOps Patterns](mlops-patterns.md) - Complete MLOps lifecycle
2. → [Model Serving](model-serving.md) - Serving infrastructure
3. → [Case Studies](../10-case-studies/) - ML monitoring in practice
