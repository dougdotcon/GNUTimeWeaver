#!/usr/bin/env python3
"""Compose healthcheck for the formal engine, not just its listening socket."""
import json
import urllib.request
from pathlib import Path

try:
    with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=3) as r:
        if r.status != 200:
            raise SystemExit(1)
    with urllib.request.urlopen("http://127.0.0.1:8000/v1/models", timeout=3) as r:
        models = json.loads(r.read())
    ids = {item.get("id") for item in models.get("data", [])}
    if "timeweaver-qwen" not in ids:
        raise SystemExit(1)
    if not Path("/results/connector_config.json").is_file():
        raise SystemExit(1)
    config = json.loads(Path("/results/connector_config.json").read_text())
    if config.get("kv_connector_extra_config", {}).get("mode") != "event_mirror_only":
        raise SystemExit(1)
except Exception:
    raise SystemExit(1)
raise SystemExit(0)
