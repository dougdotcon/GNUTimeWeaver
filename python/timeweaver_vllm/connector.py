from .errors import UnsupportedEnvironmentError
try:
    from vllm.distributed.kv_transfer.kv_connector.v1.base import KVConnectorBase_V1
except Exception:
    class KVConnectorBase_V1:
        pass

class TimeWeaverKVConnector(KVConnectorBase_V1):
    def __init__(self, vllm_config, role, kv_cache_config):
        try:
            import vllm
        except Exception as exc:
            raise UnsupportedEnvironmentError("VLLM_CONNECTOR_PROTOCOL_READY_NO_SUPPORTED_ENVIRONMENT") from exc
        super().__init__(vllm_config, role, kv_cache_config)
