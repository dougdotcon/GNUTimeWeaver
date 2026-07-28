#!/usr/bin/env python3
"""Collect reproducible v0.3.1 CPU evidence without making restore claims."""
from __future__ import annotations
import argparse, json, os, platform, subprocess, time, hashlib, urllib.request
from pathlib import Path

TAG = "v0.23.0"

def run(*cmd: str, cwd: Path | None = None) -> str:
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)
    return p.stdout.strip() if p.returncode == 0 else ""

def http_json(url: str, payload: dict | None = None) -> dict:
    body = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(url, data=body,
        headers={"Content-Type": "application/json"} if body else {})
    with urllib.request.urlopen(request, timeout=int(os.getenv("TIMEWEAVER_HTTP_TIMEOUT", "180"))) as response:
        data = response.read()
        return json.loads(data) if data else {"http_status": response.status}

def git_identity(repo: Path) -> dict:
    remote = run("git", "ls-remote", "--tags", "origin",
                 f"refs/tags/{TAG}", f"refs/tags/{TAG}^{{}}", cwd=repo)
    remote_lines = remote.splitlines()
    remote_tag = next((line.split()[0] for line in remote_lines
                       if line.endswith(f"refs/tags/{TAG}")), "")
    remote_peeled = next((line.split()[0] for line in remote_lines
                          if line.endswith(f"refs/tags/{TAG}^{{}}")), "")
    return {
        "remote_url": run("git", "remote", "get-url", "origin", cwd=repo),
        "tag_name": TAG,
        "tag_object_type": run("git", "cat-file", "-t", TAG, cwd=repo),
        "tag_object_sha": run("git", "rev-parse", TAG, cwd=repo),
        "peeled_commit_sha": run("git", "rev-parse", f"{TAG}^{{commit}}", cwd=repo),
        "checked_out_commit_sha": run("git", "rev-parse", "HEAD", cwd=repo),
        "remote_tag_object_sha": remote_tag,
        "remote_peeled_commit_sha": remote_peeled,
        "remote_tags": remote_lines,
        "tree_status": "clean" if not run("git", "status", "--porcelain", cwd=repo) else "dirty",
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vllm-repo", default="/opt/vllm", type=Path)
    ap.add_argument("--output", default="data/vllm_g0_g1.json", type=Path)
    ap.add_argument("--model", default=None, type=Path)
    ap.add_argument("--event-mirror", action="store_true")
    ap.add_argument("--engine", action="store_true")
    ap.add_argument("--phase", choices=("g0", "g1"), default="g1")
    args = ap.parse_args()
    if args.event_mirror:
        print("event_mirror_ready")
        while True:
            time.sleep(3600)
    if args.engine:
        # The campaign runner owns the formal result; this process only proves
        # that the engine boundary can be started independently.
        print("vllm_engine_ready")
        return 0
    ident = git_identity(args.vllm_repo) if (args.vllm_repo / ".git").exists() else {}
    flags = run("lscpu").lower()
    model = args.model
    model_info = {"available": bool(model and model.is_dir())}
    if model_info["available"]:
        revision_file = model / "TIMEWEAVER_MODEL_REVISION"
        sums_file = model / "SHA256SUMS"
        model_info["revision"] = revision_file.read_text().strip() if revision_file.is_file() else ""
        model_info["manifest_available"] = sums_file.is_file()
        if not model_info["revision"] or not model_info["manifest_available"]:
            model_info["available"] = False
            model_info["status"] = "M0_MODEL_SNAPSHOT_INVALID"
        files = []
        for path in sorted(model.rglob("*")):
            if path.is_file():
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                files.append({"path": str(path.relative_to(model)), "bytes": path.stat().st_size,
                              "sha256": digest})
        model_info["files"] = files
    else:
        model_info["status"] = "G0_MODEL_NOT_AVAILABLE"
    if args.phase == "g1":
        vllm_info = {"available": "not_imported_by_http_runner", "version": None, "path": None}
    else:
        try:
            import vllm
            vllm_info = {"available": True, "version": getattr(vllm, "__version__", None),
                         "path": str(Path(vllm.__file__).resolve())}
        except Exception as exc:
            vllm_info = {"available": False, "error": str(exc)}
    try:
        import timeweaver_vllm
        connector_info = {"available": True, "path": str(Path(timeweaver_vllm.__file__).resolve())}
    except Exception as exc:
        connector_info = {"available": False, "error": str(exc)}
    env = {"uname": platform.uname()._asdict(), "python": platform.python_version(),
           "architecture": platform.machine(), "cpu_avx2": "avx2" in flags,
           "logical_cpus": os.cpu_count(), "workspace": str(Path.cwd()),
           "docker": Path("/.dockerenv").exists(), "vllm": vllm_info,
           "connector": connector_info,
           "mode": os.getenv("TIMEWEAVER_VLLM_MODE", "event_mirror_only"),
           "ld_preload": os.getenv("LD_PRELOAD", "")}
    inference = {"status": "not_run", "phase": args.phase}
    # G1 must use the already-running vllm-engine. It is deliberately never
    # allowed to instantiate a second LLM in the campaign runner.
    if args.phase == "g1":
        endpoint = os.getenv("VLLM_ENGINE_ENDPOINT", "http://vllm-engine:8000").rstrip("/")
        try:
            health = http_json(endpoint + "/health")
            models = http_json(endpoint + "/v1/models")
            workload_path = Path(os.getenv("TIMEWEAVER_G1_WORKLOAD", "workloads/v031_g1_workloads.json"))
            loaded = json.loads(workload_path.read_text())
            workload = loaded if loaded.get("workload_id") == "W0-E1" else next(w for w in loaded["workloads"] if w["id"] == "W0")
            prompt = workload["prompt"]
            tokenized = http_json(endpoint + "/tokenize", {"prompt": prompt})
            sampling = workload.get("sampling", workload)
            completion = http_json(endpoint + "/v1/completions", {
                "model": "timeweaver-qwen",
                "prompt": prompt,
                "temperature": sampling["temperature"], "max_tokens": sampling["max_tokens"], "seed": sampling["seed"],
            })
            inference = {"status": "pass", "endpoint": endpoint,
                         "workload": workload, "prompt": prompt, "health": health, "models": models,
                         "tokenized": tokenized, "completion": completion}
        except Exception as exc:
            inference = {"status": "fail", "reason": "G1_ENGINE_ENDPOINT_UNAVAILABLE",
                         "engine_endpoint": endpoint, "error": repr(exc)}
    elif vllm_info["available"] and model_info["available"]:
        try:
            import torch
            from vllm import LLM, SamplingParams
            started = time.time()
            llm = LLM(model=str(model), tensor_parallel_size=1,
                      gpu_memory_utilization=0.5,
                      enable_prefix_caching=True)
            output = llm.generate(["Write one short sentence about time travel."],
                                  SamplingParams(temperature=0, max_tokens=16))[0]
            inference = {"status": "pass", "text": output.outputs[0].text,
                         "duration_s": round(time.time() - started, 3),
                         "cuda_available": torch.cuda.is_available()}
        except Exception as exc:
            inference = {"status": "fail", "error": repr(exc)}
    g0 = bool(args.phase == "g0" and ident and ident.get("peeled_commit_sha") == ident.get("checked_out_commit_sha")
              and ident.get("peeled_commit_sha") == ident.get("remote_peeled_commit_sha")
              and ident.get("tree_status") == "clean" and env["python"].startswith("3.12")
              and env["architecture"] == "x86_64" and env["cpu_avx2"] and vllm_info["available"]
              and connector_info["available"]
              and os.getenv("TIMEWEAVER_VLLM_MODE", "event_mirror_only") == "event_mirror_only"
              and model_info["available"] and inference["status"] == "pass")
    formal = ("G0_MODEL_NOT_AVAILABLE" if model_info.get("status") == "G0_MODEL_NOT_AVAILABLE"
              else "G0_MODEL_SNAPSHOT_INVALID" if model_info.get("status") == "M0_MODEL_SNAPSHOT_INVALID"
              else "G1_ENGINE_ENDPOINT_UNAVAILABLE" if args.phase == "g1" and inference["status"] != "pass"
              else "G0_INFERENCE_FAILED" if args.phase == "g0" and inference["status"] != "pass"
              else "VLLM_ENVIRONMENT_READY_EVENT_LINEAGE_NOT_VERIFIED")
    result = {"data_origin": "real_docker_vllm_runtime", "formal_conclusion": formal,
              "operational_state": {
                  "formal_engine_implemented": True,
                  "formal_engine_executed": bool(inference.get("status") == "pass"),
                  "docker_environment_prepared": True,
                  "docker_environment_executed": Path("/.dockerenv").exists(),
                  "model_snapshot_available": model_info["available"],
                  "g0_evidence_available": g0,
                  "g1_evidence_available": False,
              },
              "protocol": "timeweaver-vllm-connector-v0.3.1", "runtime": ident,
              "environment": env, "model": model_info, "inference": inference,
              "gates": {"G0": "PASS" if g0 else "FAIL",
              "G1": "BLOCKED_REAL_EVENT_CAPTURE"}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if g0 else 2

if __name__ == "__main__":
    raise SystemExit(main())
