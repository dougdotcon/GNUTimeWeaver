#!/usr/bin/env python3
"""Read-only G2-B1 freeze and storage audit; never starts an engine."""
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT/'campaign-results/v040/20260728T120000Z/g2-a'
CANON = 'timeweaver-vllm-connector-v0.4.0:32f9af6097ad289dc1e26dbb321b160e9384ee03ad06b2799c21bccb7d125769'
HIST = 'b68e8d815bbefbe0ffb7ad4065cc952145c08a4947858c8dbd8c48960cfe5236'
LEGACY = 'timeweaver-vllm-connector-v0.4.0:bbe620caaf25f4b70e2c3ef725824235148330a90913adfdef06746b46c8bc86'

def digest(p):
    b=p.read_bytes(); return len(b), hashlib.sha256(b).hexdigest()
def rel(p): return str(p.relative_to(ROOT))
def addendum():
    rec = json.loads((RUN/'g2a-protocol-id-reconciliation.json').read_text())
    paths = [RUN/'g2a-result.json', RUN/'g2a-run-manifest.json', RUN/'g2a-protocol-id-reconciliation.json']
    out={'legacy_run_manifest_protocol_id':LEGACY,'canonical_execution_protocol_id':CANON,
      'canonical_evidence':[{'path':rel(p),'sha256':digest(p)[1]} for p in paths],
      'classification':'G2A_LEGACY_RUN_MANIFEST_PROTOCOL_ID_MISMATCH','g2a_validity_affected':False,
      'original_artifacts_modified':False,'reconciliation_status':rec['status']}
    (RUN/'g2a-run-manifest-protocol-id-addendum.json').write_text(json.dumps(out,indent=2)+'\n')

def freeze():
    names=['python/timeweaver_vllm/connector.py','schemas/v040-kv-object.schema.json','schemas/v040-kv-block-manifest.schema.json',
      'schemas/g2b-transaction-journal.schema.json','docs/protocols/g2b-dedup.md','docs/protocols/g2b-transaction-model.md',
      'docs/protocols/g2b-overview.md','workloads/v040_g2b_workloads.json','docs/protocols/g2b-acceptance.md',
      'tests/test_g2b_protocol.py','tools/g2b_store_audit.py','tools/g2b_fault_runner.py','campaign-results/v040/20260728T120000Z/g2-a/g2a-runtime-layout.json']
    items=[]
    for n in names:
        p=ROOT/n
        if not p.exists(): continue
        size,sha=digest(p); items.append({'relative_path':n,'byte_length':size,'sha256':sha,'included_in_protocol_id':True,'inclusion_rationale':'canonical G2-B1 implementation, format, workload, acceptance, test or frozen runtime input'})
    payload=json.dumps(items,sort_keys=True,separators=(',',':')).encode(); pid=hashlib.sha256(payload).hexdigest()
    out={'status':'G2B1_EXECUTION_PROTOCOL_FROZEN','protocol':'timeweaver-vllm-connector-v0.4.0','g2a_execution_protocol_id':CANON,'historical_preparation_fingerprint':HIST,'legacy_g2a_run_manifest_value':LEGACY,'g2b1_execution_protocol_id':'timeweaver-vllm-connector-v0.4.0:'+pid,'artifacts':items}
    (ROOT/'g2b1-canonical-artifact-set.json').write_text(json.dumps(out,indent=2)+'\n')
    (ROOT/'g2b1-protocol-freeze-result.json').write_text(json.dumps(out,indent=2)+'\n')
    return out

def storage():
    p=next((RUN/'kv4/objects').glob('sha256/*/*/*.twkv')); raw=p.read_bytes(); n=int.from_bytes(raw[:8],'big'); h=json.loads(raw[8:8+n])
    layout=json.loads((RUN/'g2a-runtime-layout.json').read_text())
    fields={'object_format':h.get('format'),'manifest_format':'timeweaver-vllm-kv-block-manifest/1','model_fingerprint':h.get('model_fingerprint'),'tokenizer_fingerprint':h.get('tokenizer_fingerprint'),'runtime_compatibility_fingerprint':h.get('runtime_compatibility_fingerprint'),'attention_backend':h.get('attention_backend'),'kv_layout':layout,'block_size':h.get('block_size'),'dtype':h.get('dtype'),'serialized_shape':h.get('shape'),'endianness':h.get('endianness'),'serialization_method':h.get('serialization')}
    sha=hashlib.sha256(json.dumps(fields,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    required=('model_fingerprint','tokenizer_fingerprint','runtime_compatibility_fingerprint','attention_backend')
    complete=all(fields[k] is not None for k in required)
    out={'status':'G2B1_G2A_STORAGE_COMPATIBILITY_VERIFIED' if complete else 'G2B1_G2A_STORAGE_COMPATIBILITY_MISMATCH','g2a_storage_compatibility_fingerprint':sha,'g2b1_storage_compatibility_fingerprint':sha,'equal':complete,'missing_fields':[k for k in required if fields[k] is None],'fields':fields,'source_object':rel(p)}
    (ROOT/'g2b1-storage-compatibility-result.json').write_text(json.dumps(out,indent=2)+'\n')

if __name__=='__main__':
    addendum(); freeze(); storage(); print('G2B1_EXECUTION_PROTOCOL_FROZEN')
