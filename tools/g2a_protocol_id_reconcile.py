#!/usr/bin/env python3
import json
from pathlib import Path

RUN = Path('campaign-results/v040/20260728T120000Z/g2-a')
CANON = 'timeweaver-vllm-connector-v0.4.0:32f9af6097ad289dc1e26dbb321b160e9384ee03ad06b2799c21bccb7d125769'

def read_header(path):
    raw = path.read_bytes()
    size = int.from_bytes(raw[:8], 'big')
    return json.loads(raw[8:8 + size])

objects = sorted((RUN / 'kv4/objects').glob('sha256/*/*/*.twkv'))
manifests = sorted((RUN / 'kv4/manifests').glob('*.json'))
object_ids = sorted({read_header(p).get('execution_protocol_id') for p in objects})
manifest_ids = sorted({json.loads(p.read_text()).get('execution_protocol_id', json.loads(p.read_text()).get('protocol_id')) for p in manifests})
result = json.loads((RUN / 'g2a-result.json').read_text())
run_manifest = json.loads((RUN / 'g2a-run-manifest.json').read_text())
out = {
    'status': 'G2A_EXECUTION_PROTOCOL_ID_RECONCILED' if object_ids == [CANON] and manifest_ids == [CANON] else 'G2A_EXECUTION_PROTOCOL_ID_CONFLICT',
    'objects_inspected': len(objects),
    'manifests_inspected': len(manifests),
    'object_protocol_ids_unique': object_ids,
    'manifest_protocol_ids_unique': manifest_ids,
    'result_protocol_id': result.get('execution_protocol_id'),
    'run_manifest_protocol_id': run_manifest.get('execution_protocol_id'),
    'canonical_g2a_execution_protocol_id': CANON,
    'historical_preparation_fingerprints': ['b68e8d815bbefbe0ffb7ad4065cc952145c08a4947858c8dbd8c48960cfe5236'],
    'conflicts': ({'run_manifest': run_manifest.get('execution_protocol_id')} if run_manifest.get('execution_protocol_id') != CANON else {})
}
(RUN / 'g2a-protocol-id-reconciliation.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(out, indent=2))
