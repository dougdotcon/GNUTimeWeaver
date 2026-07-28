#!/usr/bin/env python3
"""G2-L0 observation hook; intentionally never writes KV payloads."""
import inspect,json,os
from pathlib import Path
def main():
 from vllm.distributed.kv_transfer.kv_connector.v1.base import KVConnectorBase_V1
 names=('register_kv_caches','register_cross_layers_kv_cache','build_connector_meta','update_state_after_alloc','save_kv_layer','wait_for_save','request_finished','get_finished','start_load_kv','wait_for_layer_load','get_num_new_matched_tokens')
 out={'status':'G2_PROTOCOL_PREPARATION_IN_PROGRESS','payload_execution':False,'prefer_cross_layer_blocks':False,'apis':{n:str(inspect.signature(getattr(KVConnectorBase_V1,n))) for n in names}}
 p=Path(os.getenv('G2_LAYOUT_RESULTS','g2-kv-layout-observation.json'));p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
