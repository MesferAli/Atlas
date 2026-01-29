# Atlas Deployment Readiness Report

**Date**: 2026-01-29
**Model**: Qwen2.5-7B (QLoRA 4-bit via Unsloth)
**Target**: RunPod GPU / Alibaba Cloud ACK (Riyadh)

---

## 1. VRAM Budget — QLoRA 4-bit Inference

| Component | Estimated VRAM |
|---|---|
| Qwen2.5-7B weights (4-bit quantized) | ~4.5 GB |
| LoRA adapter weights (r=16, 7 target modules) | ~50 MB |
| KV cache (max_seq_length=2048, single request) | ~1.5 GB |
| Tokenizer + runtime overhead | ~0.5 GB |
| CUDA context + framework | ~1.0 GB |
| **Total (single request)** | **~7.5 GB** |
| Peak with batch/concurrent requests | ~9–10 GB |

### GPU Compatibility

| GPU | VRAM | Status |
|---|---|---|
| T4 | 16 GB | Sufficient (fp16 mode) |
| A10 | 24 GB | Comfortable (bf16 mode) |
| A100 40GB | 40 GB | Recommended for production (bf16 mode) |
| L40 | 48 GB | Optimal |

The `_gpu_supports_bf16()` function in `train_model.py` auto-detects Ampere+ GPUs (compute capability >= 8.0) and selects bf16 over fp16 accordingly. The same logic applies at inference time via Unsloth's `dtype=None` auto-detection.

---

## 2. Concurrency Analysis — `/v1/chat` Endpoint

### user_role Context: SAFE

The `user_role` variable is **stack-local** within the async coroutine:

```python
# main.py:295 — local variable, not shared state
user_role = user.role.value if user else None
response = await _agent.run(request.question, user_role=user_role)
```

Each concurrent request gets its own coroutine frame with its own `user_role` binding. The value flows through `OracleSQLAgent.run()` as a function parameter and is never stored on shared state. **No risk of user_role leaking between concurrent requests.**

The deny-by-default logic is also safe:

```python
# sql_agent.py:172 — local variable
effective_role = user_role or "viewer"
```

### _prefix_cache: NEEDS FIX

`UnslothLLM._prefix_cache` is a shared mutable `dict` on the singleton LLM instance. Under concurrent async requests, multiple coroutines could read/write this dict simultaneously. While CPython's GIL prevents data corruption for dict operations, the cache could serve stale or wrong entries without proper synchronization.

**Status**: Low-severity issue. The cache is not currently used in the `generate()` method's hot path (only `_get_prefix_key()` exists but isn't called from `generate()`). However, if integrated, it would need an `asyncio.Lock`.

### model.generate(): NEEDS SERIALIZATION

The PyTorch `model.generate()` call is **not thread-safe** and **not async-safe**. Under FastAPI's async event loop, concurrent `await _agent.run()` calls could invoke `model.generate()` simultaneously on the same GPU, causing:
- CUDA errors from concurrent kernel launches
- Corrupted output tensors
- OOM from overlapping KV caches

**Fix required**: Add an `asyncio.Lock` to serialize inference calls.

---

## 3. Required Fixes

### 3.1 Add asyncio.Lock to UnslothLLM.generate()

Serializes GPU inference to prevent concurrent CUDA access:

```python
self._inference_lock = asyncio.Lock()

async def generate(self, prompt: str) -> str:
    async with self._inference_lock:
        # ... existing generate logic ...
```

### 3.2 K8s Deployment — GPU Resources

Current `k8s/deployment.yaml` allocates CPU-only resources (256Mi–512Mi RAM, no GPU). For Unsloth inference:

- Set `replicas: 1` (one model instance per GPU)
- Add `nvidia.com/gpu: 1` resource request
- Use a CUDA-enabled base image
- Increase memory limits to accommodate model loading

### 3.3 Dockerfile — CUDA Base Image

Current `Dockerfile` uses `python:3.11-slim` (CPU-only). For GPU inference, switch to:
```
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04
```
Or use the RunPod template which includes CUDA + Python pre-installed.

---

## 4. Deployment Checklist

| Item | Status |
|---|---|
| QLoRA 4-bit model fits target GPU VRAM | OK |
| `user_role` isolation under concurrency | OK — stack-local |
| Data Moat deny-by-default for unauthenticated users | OK |
| Read-only SQL validation in pipeline | OK |
| Audit logging for all queries | OK |
| `model.generate()` serialized with asyncio.Lock | **NEEDS FIX** |
| K8s GPU resource requests | **NEEDS FIX** |
| CUDA-enabled Docker image | **NEEDS FIX** |
| Column hallucination detection in eval | OK |
| bf16/fp16 auto-detection | OK |

---

## 5. Recommendation

The RAG pipeline security layer (Data Moat, read-only validation, audit logging, user_role isolation) is **production-ready**. The two blocking items for GPU deployment are:

1. **Add `asyncio.Lock`** to `UnslothLLM.generate()` — prevents concurrent CUDA crashes
2. **Update K8s manifest and Dockerfile** for GPU — enables actual model inference in production

For CPU-only deployment (using MockLLM fallback), the current configuration works as-is.
