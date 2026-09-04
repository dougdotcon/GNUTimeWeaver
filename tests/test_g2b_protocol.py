import json
from pathlib import Path
ROOT=Path(__file__).parents[1]
def test_no_execution_authorized():
    d=json.loads((ROOT/'workloads/v040_g2b_workloads.json').read_text()); assert d['execution_authorized'] is False
def test_r1_zero_new_objects():
    d=json.loads((ROOT/'workloads/v040_g2b_workloads.json').read_text()); assert d['expected']['R1_new_objects']==0
def test_journal_schema():
    d=json.loads((ROOT/'schemas/g2b-transaction-journal.schema.json').read_text()); assert d['title']=='timeweaver-kv-transaction-journal/1'
