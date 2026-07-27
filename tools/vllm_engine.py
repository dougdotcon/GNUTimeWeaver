#!/usr/bin/env python3
"""Start the single formal vLLM engine after validating its pinned CLI."""
from __future__ import annotations
import json
import os
import subprocess
from pathlib import Path

REQUIRED = ("--host", "--port", "--served-model-name",
            "--enable-prefix-caching", "--prefix-caching-hash-algo",
            "--disable-hybrid-kv-cache-manager", "--kv-transfer-config",
            "--kv-events-config")

def main() -> int:
    model = os.getenv("TIMEWEAVER_MODEL", "/models/acceptance")
    run_id = os.getenv("TIMEWEAVER_RUN_ID", "unidentified")
    results = Path(os.getenv("TIMEWEAVER_RESULTS", "/results"))
    results.mkdir(parents=True, exist_ok=True)
    preflight = subprocess.run(["python", "tools/connector_preflight.py"],
                               text=True, capture_output=True, check=False)
    (results / "connector_preflight.json").write_text(preflight.stdout + "\n",
                                                       encoding="utf-8")
    if preflight.returncode != 0:
        print(preflight.stdout, flush=True)
        return preflight.returncode
    help_result = subprocess.run(["vllm", "serve", "--help=all"], text=True,
                                 capture_output=True, check=False)
    (results / "vllm_serve_help.txt").write_text(
        help_result.stdout + help_result.stderr, encoding="utf-8")
    missing = [flag for flag in REQUIRED if flag not in help_result.stdout]
    if help_result.returncode != 0 or missing:
        print(json.dumps({"formal_conclusion": "G0_VLLM_SERVE_INTERFACE_MISMATCH",
                          "missing_flags": missing}), flush=True)
        return 20
    connector = {
        "kv_connector": "TimeWeaverKVConnector", "kv_role": "kv_both",
        "engine_id": f"timeweaver-v031-{run_id}",
        "kv_connector_module_path": "timeweaver_vllm.connector",
        "kv_load_failure_policy": "fail",
        "kv_connector_extra_config": {
            "mode": "event_mirror_only", "results_dir": str(results),
            "protocol_id": "timeweaver-vllm-connector-v0.3.1:6921ad2fb55d44c18e4c52ed83be494031c47720ef2bd8f80182d91221000985",
        },
    }
    events = {
        "enable_kv_cache_events": True, "publisher": "zmq",
        "endpoint": "tcp://*:5557", "replay_endpoint": "tcp://*:5558",
        "buffer_steps": 100, "hwm": 10000, "max_queue_size": 10000,
        "topic": "timeweaver-kv-v031",
    }
    (results / "connector_config.json").write_text(json.dumps(connector, indent=2) + "\n")
    (results / "events_config.json").write_text(json.dumps(events, indent=2) + "\n")
    command = ["vllm", "serve", model, "--host", "0.0.0.0", "--port", "8000",
               "--served-model-name", "timeweaver-qwen", "--enable-prefix-caching",
               "--gpu-memory-utilization", "0.5",
               "--prefix-caching-hash-algo", "sha256_cbor",
               "--disable-hybrid-kv-cache-manager",
               "--kv-transfer-config", json.dumps(connector),
               "--kv-events-config", json.dumps(events)]
    print(json.dumps({"engine_id": connector["engine_id"], "command": command}), flush=True)
    os.execvpe(command[0], command, os.environ.copy())
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
