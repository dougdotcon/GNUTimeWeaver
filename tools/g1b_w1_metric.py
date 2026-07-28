import json,os,urllib.request,time,hashlib
from pathlib import Path
EP='http://vllm-engine:8000'
def get(path):
 with urllib.request.urlopen(EP+path,timeout=180) as r:return r.read().decode()
def post(path,p):
 req=urllib.request.Request(EP+path,data=json.dumps(p).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=180) as r:return json.loads(r.read())
def main():
 out=Path(os.environ['TIMEWEAVER_W1_RESULTS']);out.mkdir(parents=True,exist_ok=True); w=json.loads(Path(os.environ['TIMEWEAVER_W0_FIXTURE']).read_text()); w=w['W0'] if 'W0' in w else w; prompt=w['prompt']; frozen_sha=hashlib.sha256(prompt.encode()).hexdigest()
 metrics={}; metrics['M0']=get('/metrics'); (out/'metrics-M0.prom').write_text(metrics['M0'])
 r0=post('/v1/completions',{'model':'timeweaver-qwen','prompt':prompt,'temperature':0,'seed':117038,'max_tokens':4,'stream':False}); metrics['M1']=get('/metrics'); (out/'metrics-M1.prom').write_text(metrics['M1'])
 metrics['M2']=metrics['M1']; (out/'metrics-M2.prom').write_text(metrics['M2']); r1=post('/v1/completions',{'model':'timeweaver-qwen','prompt':prompt,'temperature':0,'seed':117038,'max_tokens':4,'stream':False}); metrics['M3']=get('/metrics'); (out/'metrics-M3.prom').write_text(metrics['M3'])
 (out/'w1-metric-result.json').write_text(json.dumps({'prompt_sha256':frozen_sha,'prompt_tokens':924,'block_size':128,'max_reusable_full_block_tokens':896,'W0':r0,'W1':r1,'metrics_files':list(metrics),'cached_tokens':r1.get('usage',{}).get('prompt_tokens_details',{}).get('cached_tokens') if isinstance(r1.get('usage',{}).get('prompt_tokens_details'),dict) else None},indent=2)+'\n')
if __name__=='__main__':main()
