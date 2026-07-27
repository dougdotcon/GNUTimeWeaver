#!/usr/bin/env python3
"""Fail early when the external connector does not match the pinned vLLM API."""
from __future__ import annotations
import hashlib
import inspect
import json
from pathlib import Path

def main() -> int:
    result = {"module_path": "timeweaver_vllm.connector",
              "class_name": "TimeWeaverKVConnector"}
    try:
        from timeweaver_vllm.connector import TimeWeaverKVConnector
        from vllm.distributed.kv_transfer.kv_connector.v1.base import KVConnectorBase_V1
        result.update({
            "class_qualified_name": f"{TimeWeaverKVConnector.__module__}.{TimeWeaverKVConnector.__name__}",
            "class_mro": [c.__name__ for c in TimeWeaverKVConnector.__mro__],
            "constructor_signature": str(inspect.signature(TimeWeaverKVConnector)),
            "kv_cache_config_parameter": "kv_cache_config" in inspect.signature(TimeWeaverKVConnector).parameters,
            "source_file": inspect.getsourcefile(TimeWeaverKVConnector),
            "source_sha256": hashlib.sha256(Path(inspect.getsourcefile(TimeWeaverKVConnector)).read_bytes()).hexdigest(),
            "inherits_base": issubclass(TimeWeaverKVConnector, KVConnectorBase_V1),
        })
    except ImportError as exc:
        result.update({"status": "G0_CONNECTOR_MODULE_IMPORT_FAILED", "error": repr(exc)})
    except AttributeError as exc:
        result.update({"status": "G0_CONNECTOR_CLASS_NOT_EXPORTED", "error": repr(exc)})
    except Exception as exc:
        result.update({"status": "G0_CONNECTOR_WRONG_BASE_CLASS", "error": repr(exc)})
    else:
        result["status"] = ("PASS" if result["inherits_base"] and result["kv_cache_config_parameter"]
                            else "G0_CONNECTOR_CONSTRUCTOR_INCOMPATIBLE"
                            if not result["kv_cache_config_parameter"]
                            else "G0_CONNECTOR_WRONG_BASE_CLASS")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 21

if __name__ == "__main__":
    raise SystemExit(main())
