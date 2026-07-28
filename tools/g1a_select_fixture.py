#!/usr/bin/env python3
import hashlib, json, os, urllib.request
from pathlib import Path
def post(prompt):
    req=urllib.request.Request('http://vllm-engine:8000/tokenize',data=json.dumps({'prompt':prompt}).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=30) as r:return json.loads(r.read())
def main():
    out=Path(os.environ['TIMEWEAVER_FIXTURE_DIR']); out.mkdir(parents=True,exist_ok=True)
    source_path=Path('/results/v031/20260727T202251Z/g0-apc-supplement/g0_apc_workload.json'); source_sha=hashlib.sha256(source_path.read_bytes()).hexdigest(); source=json.loads(source_path.read_text()); text=source['prompt_r0']
    units=[u.strip()+('.' if not u.strip().endswith('.') else '') for u in text.split('.') if u.strip()]
    block_size=int(os.environ.get('TIMEWEAVER_BLOCK_SIZE','128')); selected=None; candidates=[]
    for n in range(1,len(units)+1):
        candidate=' '.join(units[:n]); tok=post(candidate); ids=tok.get('tokens',[]); candidates.append({'units':n,'tokens':len(ids)})
        if 8*block_size <= len(ids) <= 12*block_size-1:
            selected=(candidate,tok,n); break
    if selected is None:
        tok=post(text); selected=(text,tok,len(units)); candidates.append({'units':len(units),'tokens':len(tok.get('tokens',[])),'fallback':'source R0 complete'})
    prompt,tok,n=selected; frozen={'workload_id':'W0-E1','source_artifact':str(source_path), 'source_artifact_sha256':source_sha,'source_field':'prompt_r0','selection_unit_count':n,'selection_algorithm':'first natural sentence candidate in [8*block_size,12*block_size-1]','prompt':prompt,'prompt_utf8_bytes':len(prompt.encode()),'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'token_ids':tok['tokens'],'token_count':len(tok['tokens']),'block_size':block_size,'complete_blocks':len(tok['tokens'])//block_size,'tail_tokens':len(tok['tokens'])%block_size,'sampling':{'temperature':0,'seed':117038,'max_tokens':4,'stream':False},'candidates':candidates}
    (out/'w0-e1-frozen.json').write_text(json.dumps(frozen,indent=2)+'\n'); print(json.dumps(frozen,indent=2))
if __name__=='__main__':main()
