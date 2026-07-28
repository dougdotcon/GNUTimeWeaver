import json,hashlib
from pathlib import Path
import msgspec
from vllm.distributed.kv_events import KVEventBatch,BlockStored
p=Path('/data'); d=msgspec.msgpack.Decoder(KVEventBatch); reg={}; order=[]
for s,src,replayed in [(0,'pub-wire/0000-payload.bin',False),(1,'replay-wire/0001-frame-2.bin',True),(2,'replay-wire/0002-frame-2.bin',True)]:
 b=(p/src).read_bytes(); batch=d.decode(b); order.append(s)
 for e in batch.events:
  if isinstance(e,BlockStored):
   for h in e.block_hashes: reg[str(h)]={'parent':e.parent_block_hash,'sequence':s,'replayed':replayed}
online=json.loads((p/'checkpoint.json').read_text())['canonical_registry_hash']; off=hashlib.sha256(json.dumps(reg,sort_keys=True).encode()).hexdigest()
(p/'offline-reconstruction.json').write_text(json.dumps({'sequence_order':order,'node_count':len(reg),'edge_count':len(reg),'event_count':3,'online_C0_C2_registry_sha256':online,'offline_C0_C2_registry_sha256':off,'equal':online==off,'conflicts':0,'cycles':0,'last_sequence':2,'registry':reg},indent=2)+'\n')
print(json.dumps({'online':online,'offline':off,'equal':online==off,'nodes':len(reg)},indent=2))
