import json,os,urllib.request,time
from pathlib import Path
EP='http://vllm-engine:8000'
def call(path,p=None):
 r=urllib.request.Request(EP+path,data=None if p is None else json.dumps(p).encode(),headers={'Content-Type':'application/json'} if p else {})
 with urllib.request.urlopen(r,timeout=180) as x:
  b=x.read(); return json.loads(b) if b else {'status':x.status}
def main():
 out=Path(os.environ['TIMEWEAVER_G1C_RESULTS']); f=json.loads(Path(os.environ['TIMEWEAVER_G1B_FIXTURES']).read_text()); res={}
 for cid,key in [('C0','W0'),('C1','W2-A'),('C2','W2-B'),('C3','W3-A'),('C4','W3-B')]:
  w=f[key]; t=time.time(); r=call('/v1/completions',{'model':'timeweaver-qwen','prompt':w['prompt'],'temperature':0,'seed':117038,'max_tokens':4,'stream':False}); res[cid]={'workload':key,'start':t,'end':time.time(),'prompt_sha256':w['prompt_sha256'],'prompt_tokens':w['token_count'],'response':r}
 (out/'g1c-http-results.json').write_text(json.dumps(res,indent=2)+'\n'); print(json.dumps(res,indent=2))
if __name__=='__main__':main()
