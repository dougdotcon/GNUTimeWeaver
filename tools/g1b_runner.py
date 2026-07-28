#!/usr/bin/env python3
import hashlib,json,os,time,urllib.request
from pathlib import Path
EP=os.getenv('VLLM_ENGINE_ENDPOINT','http://vllm-engine:8000')
def call(path,payload=None):
 r=urllib.request.Request(EP+path,data=None if payload is None else json.dumps(payload).encode(),headers={'Content-Type':'application/json'} if payload else {})
 with urllib.request.urlopen(r,timeout=180) as x:
  b=x.read(); return json.loads(b) if b else {'status':x.status}
def main():
 out=Path(os.environ['TIMEWEAVER_G1B_RESULTS']); out.mkdir(parents=True,exist_ok=True)
 w0=json.loads(Path(os.environ['TIMEWEAVER_W0_FIXTURE']).read_text()); p0=w0['prompt']; ids0=w0['token_ids']; prefix=call('/detokenize',{'tokens':ids0[:896]})
 prefix=prefix.get('prompt',prefix.get('text','')) if isinstance(prefix,dict) else prefix
 suffixA=' Branch A deterministic continuation '+(' alpha temporal branch.'*80)
 suffixB=' Branch B deterministic continuation '+(' beta causal branch.'*80)
 suffixC=' Tail C deterministic continuation '+(' gamma partial branch.'*80)
 suffixD=' Tail D deterministic continuation '+(' delta partial branch.'*80)
 prompts={'W0':p0,'W1':p0,'W2-A':prefix+suffixA,'W2-B':prefix+suffixB,'W3-A':p0+suffixC,'W3-B':p0+suffixD}
 frozen={}
 for k,p in prompts.items():
  t=call('/tokenize',{'prompt':p}); toks=t.get('tokens',[]); frozen[k]={'prompt':p,'prompt_sha256':hashlib.sha256(p.encode()).hexdigest(),'token_ids':toks,'token_count':len(toks),'block_size':128,'complete_blocks':len(toks)//128,'tail_tokens':len(toks)%128,'sampling':{'temperature':0,'seed':117038,'max_tokens':4,'stream':False}}
 (out/'g1b-workloads-frozen.json').write_text(json.dumps(frozen,indent=2)+'\n')
 results={}
 for k,w in frozen.items():
  st=time.time(); resp=call('/v1/completions',{'model':'timeweaver-qwen','prompt':w['prompt'],'temperature':0,'seed':117038,'max_tokens':4,'stream':False}); results[k]={'request_start':st,'request_end':time.time(),'response':resp,'token_count':w['token_count']}
 (out/'g1b-http-results.json').write_text(json.dumps(results,indent=2)+'\n'); print(json.dumps({'frozen':frozen,'results':results},indent=2))
if __name__=='__main__':main()
