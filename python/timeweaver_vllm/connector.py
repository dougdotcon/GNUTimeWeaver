"""vLLM connector with frozen G1 mirror and G2-L0 metadata-only mode."""
import os
import json,time
from pathlib import Path
from .errors import UnsupportedEnvironmentError

try:
    from vllm.distributed.kv_transfer.kv_connector.v1.base import (
        KVConnectorBase_V1, KVConnectorMetadata, KVConnectorRole,
    )
    VLLM_AVAILABLE = True
except Exception:
    VLLM_AVAILABLE = False
    class KVConnectorBase_V1: pass
    class KVConnectorMetadata: pass
    class KVConnectorRole: pass

class TimeWeaverKVConnector(KVConnectorBase_V1):
    """Read-only G1 connector. It never advertises external KV tokens."""
    def __init__(self, vllm_config, role, kv_cache_config):
        if not VLLM_AVAILABLE:
            raise UnsupportedEnvironmentError("VLLM_CONNECTOR_PROTOCOL_READY_NO_SUPPORTED_ENVIRONMENT")
        if not isinstance(role, KVConnectorRole):
            raise ValueError("INVALID_CONNECTOR_ROLE")
        self.mode = os.getenv("TIMEWEAVER_VLLM_MODE", "event_mirror_only")
        if self.mode not in ("event_mirror_only", "kv_layout_observation_only"):
            raise ValueError("G2_MODE_NOT_AUTHORIZED")
        self.call_trace = []
        self.results_dir = Path(os.getenv("TIMEWEAVER_RESULTS", "/results"))
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self._layout_path = self.results_dir / "g2-l0-registered-kv-caches.json"
        self._save_path = self.results_dir / "g2-l0-save-hook-observation.jsonl"
        super().__init__(vllm_config, role, kv_cache_config)

    def _tensor_meta(self, t):
        return {"python_type":type(t).__name__,"identity":id(t),"storage_identity":id(getattr(t,'untyped_storage',lambda:None)()),"device":str(t.device),"dtype":str(t.dtype),"shape":list(t.shape),"stride":list(t.stride()),"storage_offset":int(t.storage_offset()),"element_size":int(t.element_size()),"numel":int(t.numel()),"calculated_bytes":int(t.numel()*t.element_size()),"is_contiguous":bool(t.is_contiguous()),"requires_grad":bool(t.requires_grad)}

    def get_num_new_matched_tokens(self, request, num_computed_tokens):
        self.call_trace.append("get_num_new_matched_tokens")
        return 0, False
    def update_state_after_alloc(self, request, blocks, num_external_tokens):
        self.call_trace.append("update_state_after_alloc")
    def build_connector_meta(self, scheduler_output):
        self.call_trace.append("build_connector_meta")
        return KVConnectorMetadata()
    def update_connector_output(self, connector_output):
        self.call_trace.append("update_connector_output")
    def request_finished(self, request, block_ids):
        self.call_trace.append("request_finished")
        return False, None
    def take_events(self):
        self.call_trace.append("take_events")
        return ()
    def register_kv_caches(self, kv_caches):
        self.call_trace.append("register_kv_caches")
        if self.mode == "kv_layout_observation_only":
            data={"mode":self.mode,"layers":{k:self._tensor_meta(v) for k,v in kv_caches.items()},"payload_reads":0,"payload_copies":0,"payload_writes":0}
            self._layout_path.write_text(json.dumps(data,indent=2)+"\n")
    def start_load_kv(self, forward_context, **kwargs):
        self.call_trace.append("start_load_kv")
    def wait_for_layer_load(self, layer_name):
        self.call_trace.append("wait_for_layer_load")
    def save_kv_layer(self, layer_name, kv_layer, attn_metadata, **kwargs):
        self.call_trace.append("save_kv_layer")
        if self.mode == "kv_layout_observation_only":
            rec={"timestamp":time.time(),"method":"save_kv_layer","layer_name":layer_name,"tensor":self._tensor_meta(kv_layer),"attn_metadata_type":type(attn_metadata).__name__,"kwargs":sorted(kwargs),"payload_read":False,"payload_copied":False,"payload_written":False}
            with self._save_path.open('a') as f:f.write(json.dumps(rec)+"\n")
    def wait_for_save(self):
        self.call_trace.append("wait_for_save")
    def get_finished(self, finished_req_ids):
        self.call_trace.append("get_finished")
        return set(), set()
