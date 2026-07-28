import json, os, time, urllib.request
from pathlib import Path
EP='http://vllm-engine:8000'
def call(p):
 r=urllib.request.Request(EP+'/v1/completions',data=json.dumps(p).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(r,timeout=180) as x:return json.loads(x.read())
out=Path(os.environ['TIMEWEAVER_G1C_RESULTS']); document=json.loads(Path(os.environ['TIMEWEAVER_G1B_FIXTURES']).read_text()); workloads=document['workloads']; res={}
for cid,key in [('C0','W0'),('C1','W2-A'),('C2','W2-B')]:
 w=workloads[key]; t=time.time(); r=call({'model':'timeweaver-qwen','prompt':w['prompt'],'temperature':0,'seed':117038,'max_tokens':4,'stream':False}); res[cid]={'workload':key,'start':t,'end':time.time(),'prompt_sha256':w['prompt_sha256'],'response':r}
(out/'g1c-c0-c2-http-results.json').write_text(json.dumps(res,indent=2)+'\n'); print(json.dumps(res,indent=2))
