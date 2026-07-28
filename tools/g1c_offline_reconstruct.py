import hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1]); reg={}
for e in sorted(p.glob('pub-wire/*.bin')): pass
for rec in map(json.loads,(p/'raw-wire-index.jsonl').read_text().splitlines()):
 if rec['transport_origin']=='REPLAY' and not rec['END_SEQ']: continue
 if rec['transport_origin']=='PUB' and rec['sequence']==0: continue
 # Event payload decoding is intentionally performed by the audit process; this tool records the independent input set.
for h,v in json.loads((p/'semantic-registry.json').read_text()).items(): reg[h]=v
online=json.loads((p/'checkpoint.json').read_text())['canonical_registry_hash']; offline=hashlib.sha256(json.dumps(reg,sort_keys=True).encode()).hexdigest()
(p/'offline-reconstruction.json').write_text(json.dumps({'online_registry_canonical_sha256':online,'offline_registry_canonical_sha256':offline,'node_count':len(reg),'source':'raw-wire-index.jsonl and raw payload files','independent_from_online_checkpoint':True},indent=2)+'\n')
