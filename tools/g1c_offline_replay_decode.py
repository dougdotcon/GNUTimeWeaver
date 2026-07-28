import json,hashlib
from pathlib import Path
import msgspec
from vllm.distributed.kv_events import KVEventBatch,BlockStored
p=Path('/data'); d=msgspec.msgpack.Decoder(KVEventBatch); out=[]
for s in (1,2):
 b=(p/'replay-wire'/f'{s:04d}-frame-2.bin').read_bytes(); x=d.decode(b); ev=[]
 for e in x.events:
  z={'type':type(e).__name__}
  if isinstance(e,BlockStored): z.update({'block_hashes':list(e.block_hashes),'parent_block_hash':e.parent_block_hash})
  ev.append(z)
 out.append({'sequence':s,'payload_length':len(b),'payload_sha256':hashlib.sha256(b).hexdigest(),'event_count':len(x.events),'events':ev})
(p/'offline-replay-decode.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
