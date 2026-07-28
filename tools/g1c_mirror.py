import hashlib,json,os,time,struct,tempfile
from pathlib import Path
def main():
 import zmq,msgspec
 from vllm.distributed.kv_events import KVEventBatch,BlockStored
 out=Path(os.environ['TIMEWEAVER_G1C_RESULTS']);out.mkdir(parents=True,exist_ok=True); topic=b'timeweaver-kv-v031'; eng=os.environ['TIMEWEAVER_ENGINE_ID']; ctx=zmq.Context.instance(); sub=ctx.socket(zmq.SUB);sub.connect('tcp://vllm-engine:5557');sub.setsockopt(zmq.SUBSCRIBE,topic); dec=msgspec.msgpack.Decoder(KVEventBatch); last=-1; dropped=False; records=[]; nodes={}; deadline=time.time()+int(os.getenv('TIMEWEAVER_G1C_TIMEOUT','240'))
 def checkpoint():
  data={'engine_id':eng,'last_contiguous_sequence':last,'node_count':len(nodes),'canonical_registry_hash':hashlib.sha256(json.dumps(nodes,sort_keys=True).encode()).hexdigest(),'updated_at':time.time()}; tmp=out/'checkpoint.tmp';tmp.write_text(json.dumps(data,indent=2)); os.replace(tmp,out/'checkpoint.json')
 while time.time()<deadline:
  if not sub.poll(500): continue
  frames=sub.recv_multipart(); t,s,p=frames[:3]; seq=int.from_bytes(s,'big'); rec={'origin':'PUB','sequence':seq,'frame_count':len(frames),'raw_sha256':hashlib.sha256(b''.join(frames)).hexdigest(),'received_at':time.time()}
  (out/'wire-journal.jsonl').open('a').write(json.dumps(rec)+'\n')
  if seq==1 and not dropped: dropped=True; rec['application']='controlled_drop'; records.append(rec); continue
  if seq>last+1:
   rec['application']='quarantined_gap'; records.append(rec); dealer=ctx.socket(zmq.DEALER);dealer.setsockopt(zmq.IDENTITY,b'g1c-replay-'+eng.encode());dealer.connect('tcp://vllm-engine:5558');dealer.send_multipart([b'',(last+1).to_bytes(8,'big')]);
   while True:
    rr=dealer.recv_multipart(); body=rr[-2:]; rs=int.from_bytes(body[0],'big');
    if body[0]==b'\xff'*8: break
    batch=dec.decode(body[1]);
    for e in batch.events:
     if isinstance(e,BlockStored):
      for h in e.block_hashes:nodes[str(h)]={'parent':e.parent_block_hash,'sequence':rs,'replayed':True}
    last=rs; records.append({'origin':'REPLAY','sequence':rs,'application':'replayed'}); checkpoint()
   dealer.close(0)
  if seq==last+1:
   batch=dec.decode(p)
   for e in batch.events:
    if isinstance(e,BlockStored):
     for h in e.block_hashes:nodes[str(h)]={'parent':e.parent_block_hash,'sequence':seq,'replayed':False}
   last=seq; rec['application']='applied'; records.append(rec); checkpoint()
 (out/'application-journal.json').write_text(json.dumps(records,indent=2)+'\n'); (out/'semantic-registry.json').write_text(json.dumps(nodes,indent=2)+'\n'); (out/'g1c-status.json').write_text(json.dumps({'controlled_drop_sequence':1,'gap_repaired':dropped and last>=4,'last_sequence':last,'node_count':len(nodes),'checkpoint_exists':(out/'checkpoint.json').exists()},indent=2)+'\n')
if __name__=='__main__':main()
