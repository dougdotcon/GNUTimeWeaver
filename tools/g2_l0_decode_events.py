import struct,json
import msgspec
from vllm.distributed.kv_events import KVEventBatch,BlockStored
p='/data'; d=msgspec.msgpack.Decoder(KVEventBatch); b=open(p+'/vllm_v031_w0_wire_trace.bin','rb').read();o=[];i=0
while i<len(b):
 n=struct.unpack('!I',b[i:i+4])[0];i+=4;f=[]
 for _ in range(n):
  z=struct.unpack('!I',b[i:i+4])[0];i+=4;f.append(b[i:i+z]);i+=z
 x=d.decode(f[2]);
 for e in x.events:
  if isinstance(e,BlockStored):o.append({'sequence':int.from_bytes(f[1],'big'),'block_hashes':list(e.block_hashes),'parent_block_hash':e.parent_block_hash,'token_ids':list(e.token_ids),'block_size':e.block_size,'group_idx':e.group_idx})
open(p+'/g2-l0-block-events.json','w').write(json.dumps(o,indent=2)+'\n');print(json.dumps(o,indent=2))
