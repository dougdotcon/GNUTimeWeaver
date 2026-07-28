import json,os,urllib.request,time
from pathlib import Path
def main():
 out=Path(os.environ['G2_L0_RESULTS']); fixture=json.load(open(os.environ['G2_L0_FIXTURE'])); w=fixture['W0'];
 req=urllib.request.Request('http://vllm-engine:8000/v1/completions',data=json.dumps({'model':'timeweaver-qwen','prompt':w['prompt'],'temperature':0,'seed':w['sampling']['seed'],'max_tokens':w['sampling']['max_tokens'],'stream':False}).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=300) as r: result=json.loads(r.read())
 (out/'g2-l0-http-result.json').write_text(json.dumps(result,indent=2)+'\n')
 (out/'g2-l0-runner-status.json').write_text(json.dumps({'status':'REQUEST_COMPLETED','prompt_tokens':result.get('usage',{}).get('prompt_tokens'),'expected_tokens':924},indent=2)+'\n')
if __name__=='__main__':main()
