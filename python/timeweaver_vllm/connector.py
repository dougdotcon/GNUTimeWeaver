"""vLLM v0.23.0 event-mirror-only connector."""
import os
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
        if os.getenv("TIMEWEAVER_VLLM_MODE", "event_mirror_only") != "event_mirror_only":
            raise ValueError("G2_RESTORE_MODE_NOT_AUTHORIZED")
        self.call_trace = []
        super().__init__(vllm_config, role, kv_cache_config)

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
    def start_load_kv(self, forward_context, **kwargs):
        self.call_trace.append("start_load_kv")
    def wait_for_layer_load(self, layer_name):
        self.call_trace.append("wait_for_layer_load")
    def save_kv_layer(self, layer_name, kv_layer, attn_metadata, **kwargs):
        self.call_trace.append("save_kv_layer")
    def wait_for_save(self):
        self.call_trace.append("wait_for_save")
    def get_finished(self, finished_req_ids):
        self.call_trace.append("get_finished")
        return set(), set()
