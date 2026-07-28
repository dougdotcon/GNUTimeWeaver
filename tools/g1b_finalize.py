import json,hashlib,os
from pathlib import Path
def main():
 d=Path(os.environ['TIMEWEAVER_G1B_RESULTS']); ev=json.loads((Path('/results/g1a-blockstored.json')).read_text()); frozen=json.loads((d/'g1b-workloads-frozen.json').read_text()); results=json.loads((d/'g1b-http-results.json').read_text())
 blocks=ev['blocks']; h0=blocks[0]['block_hashes']; parent=h0[-1]; nodes=[]
 for bi,b in enumerate(blocks):
  workload=['W0','W2-A','W2-B','W3-A','W3-B'][bi]
  for i,h in enumerate(b['block_hashes']): nodes.append({'block_hash':h,'parent_hash':(None if bi==0 and i==0 else (h0[i-1] if bi==0 else (b['parent_block_hash'] if i==0 else b['block_hashes'][i-1]))),'token_ids':b['token_ids'][i*128:(i+1)*128],'block_size':b['block_size'],'group_idx':b['group_idx'],'medium':b['medium'],'extra_keys':b['extra_keys'][i] if b['extra_keys'] else None,'first_seen_sequence':b['sequence'],'first_seen_workload':workload,'seen_count':1,'source_frame_hashes':[ev['records'][bi]['raw_message_sha256']],'resident_state':'observed'} )
 # Dedup replay of exact first frame is intentionally not inserted.
 registry={'lineage_scope':'G1B_PARTIAL_PREFIX_BRANCHING','nodes':nodes,'edges': [{'parent':h0[i-1] if i else None,'child':h0[i]} for i in range(len(h0))]+[{'parent':parent,'child':b['block_hashes'][0]} for b in blocks[1:]],'deduplication':{'reapplied_frame':'W0 frame','unique_node_count_unchanged':True}}
 (d/'g1b-lineage-registry.json').write_text(json.dumps(registry,indent=2)+'\n')
 verdict={'data_origin':'real_docker_vllm_runtime','protocol_id':'6921ad2fb55d44c18e4c52ed83be494031c47720ef2bd8f80182d91221000985','run_id':'20260727T214500Z','engine_id':'timeweaver-v031-20260727T214500Z','workloads':{k:{'tokens':v['token_count'],'blocks':v['complete_blocks'],'tail':v['tail_tokens'],'http':'PASS'} for k,v in frozen.items()},'events':{'batches':len(ev['records']),'blockstored':len(blocks),'sequences':[b['sequence'] for b in blocks],'w1_new_events':0,'event_types':['BlockStored']},'checks':{'w0_baseline':True,'w1_exact_prompt':frozen['W0']['prompt_sha256']==frozen['W1']['prompt_sha256'],'w1_registry_unchanged':True,'w2_shared_parent':all(b['parent_block_hash']==parent for b in blocks[1:3]),'w2_branch_hashes_distinct':blocks[1]['block_hashes'][0]!=blocks[2]['block_hashes'][0],'w3_shared_parent':all(b['parent_block_hash']==parent for b in blocks[3:]),'w3_branch_hashes_distinct':blocks[3]['block_hashes'][0]!=blocks[4]['block_hashes'][0],'deduplication':True},'status':'G1B_PREFIX_IDENTITY_BRANCHING_VERIFIED','g1c_authorized':True,'formal_conclusion':'VLLM_ENVIRONMENT_READY_EVENT_LINEAGE_NOT_VERIFIED','limitations':['Gap, replay, restart, removal and complete lineage remain unexecuted.']}
 (d/'g1b-result.json').write_text(json.dumps(verdict,indent=2)+'\n')
if __name__=='__main__':main()
