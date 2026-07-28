#!/usr/bin/env python3
import hashlib,json,sys
from pathlib import Path
def fail(code,**kw): print(json.dumps({'status':code,**kw},indent=2)); return 1
def main(path):
 p=Path(path)
 if not p.is_file(): return fail('G1C_FIXTURE_DOCUMENT_INVALID',reason='fixture file missing')
 try:d=json.loads(p.read_text())
 except Exception as e:return fail('G1C_FIXTURE_DOCUMENT_INVALID',reason=str(e))
 if not isinstance(d,dict): return fail('G1C_FIXTURE_DOCUMENT_INVALID')
 w=d.get('workloads')
 if w is None:return fail('G1C_FIXTURE_WORKLOADS_CONTAINER_MISSING')
 if not isinstance(w,dict):return fail('G1C_FIXTURE_WORKLOADS_CONTAINER_INVALID')
 miss=[x for x in ('W0','W2-A','W2-B') if x not in w]
 if miss:return fail('G1C_REQUIRED_WORKLOAD_MISSING',missing_workloads=miss)
 for k in ('W0','W2-A','W2-B'):
  if not isinstance(w[k].get('prompt'),str):return fail('G1C_FIXTURE_PROMPT_INVALID',workload=k)
 result={'status':'G1C_FIXTURE_PREFLIGHT_PASSED','fixture_path':str(p),'fixture_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'schema':'root.workloads.{W0,W2-A,W2-B}','workloads':{k:{'source':'workloads.'+k,'prompt_sha256':w[k].get('prompt_sha256'),'sampling':w[k].get('sampling')} for k in ('W0','W2-A','W2-B')}}
 print(json.dumps(result,indent=2)); return 0
if __name__=='__main__':sys.exit(main(sys.argv[1]))
