# Model Serving & Inference

Designing systems to serve ML models at scale with low latency.

---

## Serving Patterns

### Real-Time (Online) Inference

```
Request → Model → Response

┌──────────┐    ┌─────────────┐    ┌──────────────┐
│  Client  │───>│   Gateway   │───>│    Model     │
│          │<───│             │<───│   Server     │
└──────────┘    └─────────────┘    └──────────────┘
                                         │
                                         ▼
                                   ┌──────────────┐
                                   │   Feature    │
                                   │    Store     │
                                   └──────────────┘

Characteristics:
  - Synchronous request-response
  - Latency: < 100ms typical
  - Individual predictions

Use Cases:
  - Search ranking
  - Fraud detection
  - Real-time recommendations
```

### Batch Inference

```
Data → Model → Predictions → Storage

┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│  Data Lake   │───>│   Spark +   │───>│  Prediction  │
│              │    │   Model     │    │   Storage    │
└──────────────┘    └─────────────┘    └──────────────┘
                                              │
                                              ▼
                                       ┌──────────────┐
                                       │   Serving    │
                                       │   (Lookup)   │
                                       └──────────────┘

Characteristics:
  - Scheduled (hourly, daily)
  - High throughput
  - Pre-computed predictions

Use Cases:
  - Email campaigns
  - Product recommendations (pre-computed)
  - Risk scoring (daily)
```

### Streaming Inference

```
Event Stream → Model → Action Stream

┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│    Kafka     │───>│   Flink +   │───>│    Kafka     │
│   (events)   │    │   Model     │    │   (results)  │
└──────────────┘    └─────────────┘    └──────────────┘

Characteristics:
  - Near-real-time
  - Event-driven
  - Continuous processing

Use Cases:
  - Anomaly detection
  - Real-time personalization
  - IoT predictions
```

---

## Serving Infrastructure

### Model Server Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Model Serving System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Load      │───>│   Model     │───>│   Model     │         │
│  │  Balancer   │    │   Router    │    │  Instances  │         │
│  └─────────────┘    └─────────────┘    └──────┬──────┘         │
│                                               │                 │
│         ┌─────────────────────────────────────┤                 │
│         │                                     │                 │
│         ▼                                     ▼                 │
│  ┌─────────────┐                      ┌─────────────┐          │
│  │   Model     │                      │   Feature   │          │
│  │  Registry   │                      │   Store     │          │
│  └─────────────┘                      └─────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Components:
  - Load Balancer: Distribute requests
  - Model Router: Version routing, A/B testing
  - Model Instances: Actual inference
  - Model Registry: Model artifacts and metadata
  - Feature Store: Feature retrieval
```

### Model Serving Frameworks

```
Framework        │ Strength                 │ Use Case
─────────────────┼──────────────────────────┼─────────────────────
TensorFlow Serving│ TF models, gRPC         │ TensorFlow ecosystem
TorchServe       │ PyTorch models           │ PyTorch ecosystem
Triton           │ Multi-framework, GPU     │ High performance
Seldon           │ Kubernetes native        │ K8s deployments
KServe           │ Serverless inference     │ K8s, auto-scaling
BentoML          │ Easy packaging           │ Rapid deployment
Ray Serve        │ Scalable, flexible       │ Complex pipelines
```

### Containerized Deployment

```
Model Container:
  ┌─────────────────────────────────────────────────┐
  │                 Model Container                  │
  │  ┌───────────────────────────────────────────┐ │
  │  │           Runtime (Python, etc.)          │ │
  │  ├───────────────────────────────────────────┤ │
  │  │           ML Framework                     │ │
  │  │        (TensorFlow, PyTorch)              │ │
  │  ├───────────────────────────────────────────┤ │
  │  │           Model Weights                   │ │
  │  │         (downloaded or baked in)          │ │
  │  ├───────────────────────────────────────────┤ │
  │  │           Server Code                     │ │
  │  │    (HTTP/gRPC server, preprocessing)      │ │
  │  └───────────────────────────────────────────┘ │
  └─────────────────────────────────────────────────┘

Kubernetes Deployment:
  - Deployment with replicas
  - Horizontal Pod Autoscaler (HPA)
  - GPU node pools for deep learning
```

---

## Optimization Techniques

### Model Optimization

```
1. Quantization:
   - Reduce precision (FP32 → INT8)
   - 2-4x smaller model
   - 2-4x faster inference
   - Small accuracy loss

2. Pruning:
   - Remove unimportant weights
   - Reduce model size
   - Maintain accuracy

3. Knowledge Distillation:
   - Train smaller model to mimic larger
   - Student learns from teacher
   - Significant size reduction

4. Compilation:
   - TensorRT (NVIDIA)
   - ONNX Runtime
   - Apache TVM
   - Hardware-specific optimization
```

### Serving Optimization

```
Batching:
  - Group requests for efficient GPU use
  - Dynamic batching (wait for batch)
  - Throughput vs latency trade-off

  Config example:
    max_batch_size: 32
    batch_timeout_ms: 10

Caching:
  - Cache frequent predictions
  - Embedding caching
  - Feature caching

  Cache layers:
    Request → Cache → Model

    If cache hit: return cached
    Else: compute, cache, return

Model Warmup:
  - Pre-load models into memory
  - Run dummy predictions
  - Avoid cold start latency
```

### Hardware Selection

```
Workload         │ Hardware            │ When to Use
─────────────────┼─────────────────────┼─────────────────────
Simple models    │ CPU                 │ Linear, tree-based
Medium models    │ GPU (T4, A10)       │ Neural networks
Large models     │ GPU (A100, H100)    │ Transformers, LLMs
Inference only   │ Inference chips     │ High volume
                 │ (AWS Inferentia)    │
Edge deployment  │ Mobile chips        │ On-device inference
                 │ (TPU, Neural Engine)│
```

---

## Deployment Strategies

### Canary Deployment

```
     100% traffic
          │
    ┌─────▼─────┐
    │    v1     │  ← Current version
    └───────────┘
          │
    Start canary
          │
    ┌─────▼─────┐     ┌───────────┐
    │    v1     │     │    v2     │
    │   (95%)   │     │   (5%)    │  ← Canary
    └───────────┘     └───────────┘
          │
    Monitor metrics
          │
    ┌─────▼─────┐     ┌───────────┐
    │    v1     │     │    v2     │
    │   (0%)    │     │  (100%)   │  ← Full rollout
    └───────────┘     └───────────┘

Metrics to monitor:
  - Error rate
  - Latency
  - Business metrics (CTR, conversion)
```

### Shadow Deployment

```
Request ──┬──> v1 (production) ──> Response
          │
          └──> v2 (shadow) ──> Logged (not returned)

Benefits:
  - No user impact
  - Real traffic testing
  - Compare predictions

Use for:
  - Validating new model
  - Comparing latency
  - Debugging differences
```

### Blue-Green Deployment

```
             ┌───────────────┐
             │   Load        │
             │   Balancer    │
             └───────┬───────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
    ▼                │                ▼
┌─────────┐          │          ┌─────────┐
│  Blue   │ ←── Traffic ───     │  Green  │
│  (v1)   │                     │  (v2)   │
└─────────┘                     └─────────┘

Switch:
  - Instant cutover
  - Easy rollback
  - Requires 2x resources
```

---

## Multi-Model Serving

### Model Ensemble

```
Request → [Model A, Model B, Model C] → Aggregation → Response

Aggregation strategies:
  - Averaging (regression)
  - Voting (classification)
  - Stacking (meta-model)
  - Weighted combination
```

### Model Chaining

```
Request → Model A → Model B → Model C → Response

Example (Search):
  Query → Query Understanding → Retrieval → Ranking → Results
              │                     │           │
              └─ Intent Model       └─ Embedding └─ Ranker Model
```

### A/B Testing

```
             ┌───────────────┐
             │   Traffic     │
             │   Splitter    │
             └───────┬───────┘
                     │
    ┌────────────────┼────────────────┐
    │ 50%            │            50% │
    ▼                │                ▼
┌─────────┐          │          ┌─────────┐
│ Model A │          │          │ Model B │
│(Control)│          │          │(Treatment)
└─────────┘          │          └─────────┘
                     │
             ┌───────▼───────┐
             │   Metrics     │
             │   Collection  │
             └───────────────┘

Requirements:
  - Consistent user bucketing
  - Statistical significance
  - Guard rails for safety
```

---

## Scaling Strategies

### Horizontal Scaling

```
               ┌─────────────────────────────────────────┐
               │         Kubernetes Cluster               │
               │                                          │
               │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐│
               │  │ Pod  │  │ Pod  │  │ Pod  │  │ Pod  ││
               │  │  v1  │  │  v1  │  │  v1  │  │  v1  ││
               │  └──────┘  └──────┘  └──────┘  └──────┘│
               │                                          │
               │  HPA: Scale based on CPU/Memory/Custom   │
               └─────────────────────────────────────────┘

Auto-scaling config:
  minReplicas: 2
  maxReplicas: 100
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

### GPU Sharing

```
Multiple models on single GPU:
  - NVIDIA MPS (Multi-Process Service)
  - Time-slicing
  - Memory partitioning (MIG on A100)

Benefits:
  - Better GPU utilization
  - Cost efficiency
  - Lower latency for small models
```

---

## Interview Tips

### Questions to Ask

```
1. What's the latency requirement?
   → Determines serving architecture

2. What's the prediction volume?
   → Sizing and scaling strategy

3. How often does the model update?
   → Deployment strategy

4. What's the model size and type?
   → Hardware and optimization

5. Is there multi-model coordination?
   → Ensemble or chaining needs
```

### Key Points to Discuss

```
✓ Real-time vs batch decision
✓ Model optimization techniques
✓ Deployment strategy (canary, shadow)
✓ Scaling approach
✓ Feature serving integration
✓ Latency budget breakdown
```

---

## Next Steps

1. → [ML Monitoring](ml-monitoring.md) - Monitor model performance
2. → [MLOps Patterns](mlops-patterns.md) - End-to-end MLOps
3. → [Case Studies](../10-case-studies/) - ML systems in practice
