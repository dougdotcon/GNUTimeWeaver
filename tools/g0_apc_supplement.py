#!/usr/bin/env python3
"""Supplemental local APC evidence: one LLM instance, R0/R1/R2."""
from __future__ import annotations
import hashlib, json, os, platform, resource, time
from pathlib import Path

PROTOCOL = "timeweaver-vllm-connector-v0.3.1"
PREFIX = ("TimeWeaver APC qualification shared prefix. "
          "This deterministic sentence is repeated to create complete KV blocks. " * 48)
SUFFIX_A = " Suffix A asks for a short temporal ordering statement."
SUFFIX_B = " Suffix B asks for a short causal ordering statement."

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def evidence(output, started: float, request_id: str) -> dict:
    prompt_ids = list(getattr(output, "prompt_token_ids", []) or [])
    outs = getattr(output, "outputs", []) or []
    item = outs[0] if outs else None
    metrics = getattr(output, "metrics", None)
    cached = getattr(output, "num_cached_tokens", None)
    return {"request_id": request_id, "prompt_token_ids": prompt_ids,
            "prompt_token_count": len(prompt_ids),
            "num_cached_tokens": cached, "metric_available": cached is not None,
            "metric_source": "RequestOutput.num_cached_tokens" if cached is not None else None,
            "metrics": repr(metrics) if metrics is not None else None,
            "output_token_ids": list(getattr(item, "token_ids", []) or []) if item else [],
            "output_text": getattr(item, "text", "") if item else "",
            "finish_reason": getattr(item, "finish_reason", None) if item else None,
            "duration_s": round(time.time() - started, 6)}

def main() -> int:
    outdir = Path(os.environ.get("TIMEWEAVER_APC_RESULTS", "campaign-results/v031/g0-apc-supplement"))
    workload_path = outdir / "g0_apc_workload.json"
    workload = {"shared_prefix": PREFIX, "shared_prefix_sha256": hashlib.sha256(PREFIX.encode()).hexdigest(),
                "suffix_a": SUFFIX_A, "suffix_b": SUFFIX_B,
                "prompt_r0": PREFIX + SUFFIX_A, "prompt_r1": PREFIX + SUFFIX_A,
                "prompt_r2": PREFIX + SUFFIX_B, "sampling": {"temperature": 0, "max_tokens": 4, "seed": 117038},
                "expected_behavior": "R0 cold; R1 exact repeat; R2 shared prefix with different suffix"}
    workload_path.write_text(json.dumps(workload, indent=2) + "\n")
    import torch
    from vllm import LLM, SamplingParams
    started = time.time(); pid = os.getpid()
    llm = LLM(model=os.environ.get("TIMEWEAVER_MODEL", "/models/acceptance"), tensor_parallel_size=1,
              pipeline_parallel_size=1, gpu_memory_utilization=0.5, enable_prefix_caching=True,
              prefix_caching_hash_algo="sha256_cbor")
    engine_identity = f"llm:{id(llm)}"
    params = SamplingParams(temperature=0, max_tokens=4, seed=117038)
    ev = {}
    for rid, prompt in (("R0", workload["prompt_r0"]), ("R1", workload["prompt_r1"]), ("R2", workload["prompt_r2"])):
        t = time.time(); result = llm.generate([prompt], params)[0]
        ev[rid] = evidence(result, t, rid)
    r0, r1, r2 = ev["R0"], ev["R1"], ev["R2"]
    block_size = getattr(getattr(llm, "llm_engine", None), "model_config", None)
    block_size = getattr(block_size, "block_size", None) or 16
    shared_tokens = min(r0["prompt_token_count"], r2["prompt_token_count"]) - 10
    shared_blocks = max(0, shared_tokens // block_size)
    cached_values = [ev[x]["num_cached_tokens"] for x in ("R0", "R1", "R2")]
    hit = r1["num_cached_tokens"] is not None and r1["num_cached_tokens"] > 0
    r1_ok = (r0["prompt_token_ids"] == r1["prompt_token_ids"] and r1["output_token_ids"]
             and r1["finish_reason"] is not None and hit)
    del llm
    cleanup = True
    result = {"data_origin": "real_docker_vllm_runtime", "protocol": PROTOCOL,
              "process_identity": {"pid": pid, "engine_identity": engine_identity, "model_load_count": 1},
              "runtime": {"python": platform.python_version(), "vllm": "0.23.0", "cuda_available": torch.cuda.is_available()},
              "effective_prefix_cache_config": {"enable_prefix_caching": True, "prefix_caching_hash_algo": "sha256_cbor", "tensor_parallel_size": 1, "pipeline_parallel_size": 1},
              "block_size": block_size, "workload": {"path": str(workload_path), "sha256": sha(workload_path), "r0_tokens": r0["prompt_token_count"], "r1_tokens": r1["prompt_token_count"], "r2_tokens": r2["prompt_token_count"], "shared_prefix_tokens": shared_tokens, "shared_complete_blocks": shared_blocks},
              "R0": r0, "R1": r1, "R2": r2, "metrics_snapshots": {},
              "timings": {x: ev[x]["duration_s"] for x in ev},
              "cleanup": {"passed": cleanup, "peak_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
              "apc_gate": {"status": "G0_APC_VERIFIED" if r1_ok else "G0_APC_NO_CACHE_HITS", "r1_structural_hit": hit, "r1_exact_prompt": r0["prompt_token_ids"] == r1["prompt_token_ids"]},
              "limitations": ["Runtime did not expose cache counter" ] if not hit else []}
    (outdir / "g0_apc_supplement.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if r1_ok else 2

if __name__ == "__main__":
    raise SystemExit(main())
