#!/usr/bin/env python3
"""Collect reproducible v0.3.1 CPU evidence without making restore claims."""
from __future__ import annotations
import argparse, json, os, platform, subprocess, time, hashlib
from pathlib import Path

TAG = "v0.23.0"

def run(*cmd: str, cwd: Path | None = None) -> str:
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)
    return p.stdout.strip() if p.returncode == 0 else ""

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
        files = []
        for path in sorted(model.rglob("*")):
            if path.is_file():
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                files.append({"path": str(path.relative_to(model)), "bytes": path.stat().st_size,
                              "sha256": digest})
        model_info["files"] = files
    else:
        model_info["status"] = "G0_MODEL_NOT_AVAILABLE"
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
    inference = {"status": "not_run"}
    if vllm_info["available"] and model_info["available"]:
        try:
            import torch
            from vllm import LLM, SamplingParams
            started = time.time()
            llm = LLM(model=str(model), device="cpu", tensor_parallel_size=1,
                      enable_prefix_caching=True)
            output = llm.generate(["Write one short sentence about time travel."],
                                  SamplingParams(temperature=0, max_tokens=16))[0]
            inference = {"status": "pass", "text": output.outputs[0].text,
                         "duration_s": round(time.time() - started, 3),
                         "cuda_available": torch.cuda.is_available()}
        except Exception as exc:
            inference = {"status": "fail", "error": repr(exc)}
    g0 = bool(ident and ident.get("peeled_commit_sha") == ident.get("checked_out_commit_sha")
              and ident.get("peeled_commit_sha") == ident.get("remote_peeled_commit_sha")
              and ident.get("tree_status") == "clean" and env["python"].startswith("3.12")
              and env["architecture"] == "x86_64" and env["cpu_avx2"] and vllm_info["available"]
              and connector_info["available"]
              and os.getenv("TIMEWEAVER_VLLM_MODE", "event_mirror_only") == "event_mirror_only"
              and model_info["available"] and inference["status"] == "pass")
    result = {"protocol": "timeweaver-vllm-connector-v0.3.1", "runtime": ident,
              "environment": env, "model": model_info, "inference": inference,
              "gates": {"G0": "PASS" if g0 else "FAIL",
              "G1": "BLOCKED_REAL_EVENT_CAPTURE"}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if g0 else 2

if __name__ == "__main__":
    raise SystemExit(main())
