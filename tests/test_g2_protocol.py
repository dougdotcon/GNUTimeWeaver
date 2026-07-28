import json
from pathlib import Path
ROOT=Path(__file__).parents[1]
def test_g2_workload_is_not_authorized():
 d=json.loads((ROOT/'workloads/v040_g2_workloads.json').read_text()); assert d['execution_authorized'] is False
def test_object_schema_version():
 d=json.loads((ROOT/'schemas/v040-kv-object.schema.json').read_text()); assert d['title']=='timeweaver-vllm-kv-object/1'
def test_manifest_schema_version():
 d=json.loads((ROOT/'schemas/v040-kv-block-manifest.schema.json').read_text()); assert d['title']=='timeweaver-vllm-kv-block-manifest/1'
def test_g1_remains_frozen():
 assert Path(ROOT/'campaign-results/v031/20260728T050000Z/g1-c-hash-supplement/g1c-composite-verdict.json').exists()
