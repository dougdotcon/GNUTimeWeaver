#!/usr/bin/env python3
"""G1-C C0-C2 mirror with lossless wire capture before decoding."""
import hashlib, json, os, time
from pathlib import Path

def sha(b): return hashlib.sha256(b).hexdigest()
def multipart_hash(frames):
    out = len(frames).to_bytes(8, 'big')
    for f in frames: out += len(f).to_bytes(8, 'big') + f
    return sha(out)

def main():
    import zmq, msgspec
    from vllm.distributed.kv_events import KVEventBatch, BlockStored
    out = Path(os.environ['TIMEWEAVER_G1C_RESULTS']); out.mkdir(parents=True, exist_ok=True)
    pubdir, repdir = out/'pub-wire', out/'replay-wire'; pubdir.mkdir(exist_ok=True); repdir.mkdir(exist_ok=True)
    topic = b'timeweaver-kv-v031'; eng = os.environ['TIMEWEAVER_ENGINE_ID']
    ctx=zmq.Context.instance(); sub=ctx.socket(zmq.SUB); sub.connect('tcp://vllm-engine:5557'); sub.setsockopt(zmq.SUBSCRIBE, topic)
    dec=msgspec.msgpack.Decoder(KVEventBatch); last=-1; dropped=False; records=[]; nodes={}; index=[]; deadline=time.time()+int(os.getenv('TIMEWEAVER_G1C_TIMEOUT','300'))
    def save(origin, ordinal, frames, seq=None, end=False, applied=False, quarantined=False, controlled_drop=False):
        d = pubdir if origin=='PUB' else repdir
        paths=[]
        for i,f in enumerate(frames):
            name = f'{ordinal:04d}-'+(('topic' if i==0 else 'sequence' if origin=='PUB' and i==1 else 'payload' if origin=='PUB' and i==2 else f'frame-{i}') )+'.bin'
            p=d/name; p.write_bytes(f); paths.append(str(p))
        index.append({'transport_origin':origin,'ordinal':ordinal,'received_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'frame_count':len(frames),'frame_lengths':[len(f) for f in frames],'frame_sha256':[sha(f) for f in frames],'raw_multipart_sha256':multipart_hash(frames),'sequence':seq,'END_SEQ':end,'applied':applied,'quarantined':quarantined,'controlled_drop':controlled_drop,'paths':paths})
    def apply_payload(payload, seq, replayed):
        batch=dec.decode(payload)
        for e in batch.events:
            if isinstance(e, BlockStored):
                for h in e.block_hashes: nodes[str(h)]={'parent':e.parent_block_hash,'sequence':seq,'replayed':replayed}
        return batch
    def checkpoint():
        data={'engine_id':eng,'last_contiguous_sequence':last,'node_count':len(nodes),'canonical_registry_hash':sha(json.dumps(nodes,sort_keys=True).encode()),'updated_at':time.time()}
        (out/'checkpoint.json').write_text(json.dumps(data,indent=2)+'\n')
    while time.time()<deadline:
        if not sub.poll(500): continue
        frames=sub.recv_multipart(); seq=int.from_bytes(frames[1],'big'); save('PUB',seq,frames,seq,controlled_drop=(seq==1 and not dropped),quarantined=(seq>last+1))
        if seq==1 and not dropped: dropped=True; records.append({'origin':'PUB','sequence':1,'application':'controlled_drop'}); continue
        if seq>last+1:
            records.append({'origin':'PUB','sequence':seq,'application':'quarantined_gap','expected':last+1,'observed':seq})
            dealer=ctx.socket(zmq.DEALER); dealer.setsockopt(zmq.IDENTITY,('g1c-hash-'+eng).encode()); dealer.connect('tcp://vllm-engine:5558'); dealer.send_multipart([b'',(last+1).to_bytes(8,'big')]); ro=0
            while True:
                rr=dealer.recv_multipart(); ro+=1
                if rr[-1] == b'\xff'*8:
                    save('REPLAY',ro,rr,end=True); break
                rs=int.from_bytes(rr[-2],'big'); save('REPLAY',ro,rr,seq=rs); apply_payload(rr[-1],rs,True); last=rs; records.append({'origin':'REPLAY','sequence':rs,'application':'replayed'}); checkpoint()
            dealer.close(0)
        if seq==last+1:
            apply_payload(frames[2],seq,False); last=seq; records.append({'origin':'PUB','sequence':seq,'application':'applied'}); checkpoint()
        if last>=2: break
    (out/'raw-wire-index.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in index)); (out/'application-journal.json').write_text(json.dumps(records,indent=2)+'\n'); (out/'semantic-registry.json').write_text(json.dumps(nodes,indent=2)+'\n')
    (out/'g1c-c0-c2-status.json').write_text(json.dumps({'controlled_drop_sequence':1,'gap_repaired':last>=2,'last_contiguous_sequence':last,'node_count':len(nodes),'raw_payloads_persisted':True},indent=2)+'\n')
if __name__=='__main__': main()
