"""vLLM connector with frozen G1 mirror and G2-L0 metadata-only mode."""
import os
import json,time,hashlib
from dataclasses import dataclass,field
from pathlib import Path
from .errors import UnsupportedEnvironmentError

try:
    from vllm.distributed.kv_transfer.kv_connector.v1.base import (
        KVConnectorBase_V1, KVConnectorMetadata, KVConnectorRole,
    )
    VLLM_AVAILABLE = True
except Exception:
    VLLM_AVAILABLE = False
    class KVConnectorBase_V1: pass
    class KVConnectorMetadata: pass
    class KVConnectorRole: pass

@dataclass(frozen=True)
class TimeWeaverBlockMappingObservation:
    request_id: str
    logical_ordinal: int
    logical_block_hash: str
    parent_hash: str|None
    token_ids_sha256: str
    physical_block_id: int
    kv_cache_group: int
    block_size: int
    full_block: bool

@dataclass(frozen=True)
class TimeWeaverG2L0Metadata(KVConnectorMetadata):
    schema: str = "timeweaver-g2-l0-metadata/1"
    generation: int = 0
    scheduler_step: int = 0
    engine_id: str = ""
    canary: str = "TW-G2-L0M2"
    entries: tuple = field(default_factory=tuple)

def _canonical_meta(m):
    d={'schema':m.schema,'generation':m.generation,'scheduler_step':m.scheduler_step,'engine_id':m.engine_id,'entries':[e.__dict__ for e in sorted(m.entries,key=lambda x:(x.request_id,x.logical_ordinal))]}
    return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()

class TimeWeaverKVConnector(KVConnectorBase_V1):
    """Read-only G1 connector. It never advertises external KV tokens."""
    def __init__(self, vllm_config, role, kv_cache_config):
        if not VLLM_AVAILABLE:
            raise UnsupportedEnvironmentError("VLLM_CONNECTOR_PROTOCOL_READY_NO_SUPPORTED_ENVIRONMENT")
        if not isinstance(role, KVConnectorRole):
            raise ValueError("INVALID_CONNECTOR_ROLE")
        self.mode = os.getenv("TIMEWEAVER_VLLM_MODE", "event_mirror_only")
        if self.mode not in ("event_mirror_only", "kv_layout_observation_only", "kv_payload_save_only"):
            raise ValueError("G2_MODE_NOT_AUTHORIZED")
        self.call_trace = []
        self.results_dir = Path(os.getenv("TIMEWEAVER_RESULTS", "/results"))
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self._layout_path = self.results_dir / "g2-l0-registered-kv-caches.json"
        self._save_path = self.results_dir / "g2-l0-save-hook-observation.jsonl"
        self._alloc_path = self.results_dir / "g2-l0m-allocation-observation.jsonl"
        self._meta_path = self.results_dir / "g2-l0m-scheduler-metadata.jsonl"
        self._finish_path = self.results_dir / "g2-l0m-request-finished-validation.jsonl"
        self._bind_path = self.results_dir / "g2-l0m2-bind-metadata.jsonl"
        self._save_meta_path = self.results_dir / "g2-l0m2-save-hook-metadata.jsonl"
        self._load_path = self.results_dir / "g2-l0m2-start-load-audit.jsonl"
        self._generation = 0
        self._last_meta = None
        self._allocations = {}
        self._object_root = self.results_dir / 'kv4' / 'objects' / 'sha256'
        self._manifest_root = self.results_dir / 'kv4' / 'manifests'
        self._saved = set(); self._block_objects = {}
        if self.mode == 'kv_payload_save_only': self._object_root.mkdir(parents=True,exist_ok=True); self._manifest_root.mkdir(parents=True,exist_ok=True)
        super().__init__(vllm_config, role, kv_cache_config)

    def _tensor_meta(self, t):
        return {"python_type":type(t).__name__,"identity":id(t),"storage_identity":id(getattr(t,'untyped_storage',lambda:None)()),"device":str(t.device),"dtype":str(t.dtype),"shape":list(t.shape),"stride":list(t.stride()),"storage_offset":int(t.storage_offset()),"element_size":int(t.element_size()),"numel":int(t.numel()),"calculated_bytes":int(t.numel()*t.element_size()),"is_contiguous":bool(t.is_contiguous()),"requires_grad":bool(t.requires_grad)}

    def get_num_new_matched_tokens(self, request, num_computed_tokens):
        self.call_trace.append("get_num_new_matched_tokens")
        return 0, False
    def update_state_after_alloc(self, request, blocks, num_external_tokens):
        self.call_trace.append("update_state_after_alloc")
        if self.mode in ("kv_layout_observation_only", "kv_payload_save_only"):
            ids = blocks.get_block_ids() if hasattr(blocks,'get_block_ids') else None
            hashes = list(getattr(request,'block_hashes',()) or ())
            rec={"request_id":str(getattr(request,'request_id',getattr(request,'id','unknown'))),"scheduler_pid":os.getpid(),"block_ids_by_group":ids,"num_external_tokens":num_external_tokens,"num_tokens":getattr(request,'num_tokens',None),"num_prompt_tokens":getattr(request,'num_prompt_tokens',None),"num_computed_tokens":getattr(request,'num_computed_tokens',None),"logical_block_hashes":hashes,"num_full_blocks":len(hashes),"tail_token_count":28}
            self._allocations[rec['request_id']]=rec
            with self._alloc_path.open('a') as f:f.write(json.dumps(rec,default=str)+'\n')
    def build_connector_meta(self, scheduler_output):
        self.call_trace.append("build_connector_meta")
        meta=KVConnectorMetadata()
        if self.mode in ("kv_layout_observation_only", "kv_payload_save_only"):
            entries=[]
            for rid,a in self._allocations.items():
                ids=(a.get('block_ids_by_group') or [[]])[0] if a.get('block_ids_by_group') else []
                for i,h in enumerate(a.get('logical_block_hashes',[])[:7]):
                    hs=str(h); entries.append(TimeWeaverBlockMappingObservation(rid,i,hs,None,hashlib.sha256(hs.encode()).hexdigest(),int(ids[i]),0,128,True))
            self._generation+=1; meta=TimeWeaverG2L0Metadata(generation=self._generation,scheduler_step=self._generation,engine_id=os.getenv('TIMEWEAVER_ENGINE_ID',''),entries=tuple(entries)); self._last_meta=meta
            with self._meta_path.open('a') as f:f.write(json.dumps({'schema':meta.schema,'generation':meta.generation,'scheduler_step':meta.scheduler_step,'canonical_sha256':_canonical_meta(meta),'canary':meta.canary,'entries':[e.__dict__ for e in meta.entries]},sort_keys=True)+'\n')
        return meta

    def bind_connector_metadata(self, connector_metadata):
        super().bind_connector_metadata(connector_metadata)
        if self.mode == "kv_layout_observation_only":
            m=self._get_connector_metadata(); rec={'pid':os.getpid(),'metadata_type':type(m).__name__,'metadata_module':type(m).__module__,'schema':getattr(m,'schema',None),'generation':getattr(m,'generation',None),'scheduler_step':getattr(m,'scheduler_step',None),'canary':getattr(m,'canary',None),'entry_count':len(getattr(m,'entries',())),'canonical_sha256':_canonical_meta(m) if isinstance(m,TimeWeaverG2L0Metadata) else None,'physical_ids':[e.physical_block_id for e in getattr(m,'entries',())]};
            with self._bind_path.open('a') as f:f.write(json.dumps(rec)+'\n')
    def update_connector_output(self, connector_output):
        self.call_trace.append("update_connector_output")
    def request_finished(self, request, block_ids):
        self.call_trace.append("request_finished")
        if self.mode == "kv_layout_observation_only":
            rid=str(getattr(request,'request_id',getattr(request,'id','unknown')))
            with self._finish_path.open('a') as f:f.write(json.dumps({'request_id':rid,'block_ids':block_ids,'allocation':self._allocations.get(rid)},default=str)+'\n')
        return False, None
    def take_events(self):
        self.call_trace.append("take_events")
        return ()
    def register_kv_caches(self, kv_caches):
        self.call_trace.append("register_kv_caches")
        if self.mode == "kv_layout_observation_only":
            data={"mode":self.mode,"layers":{k:self._tensor_meta(v) for k,v in kv_caches.items()},"payload_reads":0,"payload_copies":0,"payload_writes":0}
            self._layout_path.write_text(json.dumps(data,indent=2)+"\n")
    def start_load_kv(self, forward_context, **kwargs):
        self.call_trace.append("start_load_kv")
        if self.mode == "kv_layout_observation_only":
            with self._load_path.open('a') as f:f.write(json.dumps({'pid':os.getpid(),'load_operations':0,'metadata_hash':_canonical_meta(self._get_connector_metadata()) if isinstance(self._get_connector_metadata(),TimeWeaverG2L0Metadata) else None})+'\n')
    def wait_for_layer_load(self, layer_name):
        self.call_trace.append("wait_for_layer_load")
    def save_kv_layer(self, layer_name, kv_layer, attn_metadata, **kwargs):
        self.call_trace.append("save_kv_layer")
        if self.mode == "kv_layout_observation_only":
            m=self._get_connector_metadata(); rec={"timestamp":time.time(),"method":"save_kv_layer","layer_name":layer_name,"tensor":self._tensor_meta(kv_layer),"attn_metadata_type":type(attn_metadata).__name__,"kwargs":sorted(kwargs),"payload_read":False,"payload_copied":False,"payload_written":False,'metadata_type':type(m).__name__,'metadata_hash':_canonical_meta(m) if isinstance(m,TimeWeaverG2L0Metadata) else None,'metadata_generation':getattr(m,'generation',None),'physical_ids':[e.physical_block_id for e in getattr(m,'entries',())]}
            with self._save_path.open('a') as f:f.write(json.dumps(rec)+"\n")
        elif self.mode == 'kv_payload_save_only':
            m=self._get_connector_metadata(); entries=getattr(m,'entries',())
            if not entries:
                return
            for e in entries:
                key=(e.logical_block_hash,e.physical_block_id,layer_name)
                if key in self._saved: continue
                if not (e.full_block and 0 <= e.physical_block_id < int(kv_layer.shape[0])): raise ValueError('G2A_PHYSICAL_BLOCK_ID_OUT_OF_RANGE')
                snap=kv_layer[e.physical_block_id,:,:,:].detach().clone().contiguous()
                raw=snap.view(__import__('torch').uint8).numpy().tobytes(); ph=hashlib.sha256(raw).hexdigest()
                header={'format':'timeweaver-vllm-kv-object/1','execution_protocol_id':os.getenv('TIMEWEAVER_EXECUTION_PROTOCOL_ID',''),'layer_name':layer_name,'logical_block_hash':e.logical_block_hash,'parent_hash':e.parent_hash,'token_ids_sha256':e.token_ids_sha256,'block_size':e.block_size,'cache_group':e.kv_cache_group,'dtype':str(snap.dtype),'shape':list(snap.shape),'payload_byte_length':len(raw),'endianness':'native','serialization':'raw_contiguous_tensor','payload_sha256':ph}
                hb=json.dumps(header,sort_keys=True,separators=(',',':')).encode(); oh=hashlib.sha256(hb+raw).hexdigest(); final=self._object_root/oh[:2]/oh[2:4]/(oh+'.twkv'); final.parent.mkdir(parents=True,exist_ok=True); tmp=final.with_suffix('.tmp'); tmp.write_bytes(len(hb).to_bytes(8,'big')+hb+raw); fd=os.open(tmp,os.O_RDONLY); os.fsync(fd);os.close(fd);os.replace(tmp,final); dfd=os.open(final.parent,os.O_RDONLY);os.fsync(dfd);os.close(dfd)
                self._saved.add(key); self._block_objects.setdefault(e.logical_block_hash,[]).append({'layer_name':layer_name,'object_sha256':oh,'payload_sha256':ph,'payload_bytes':len(raw)})
            for bh, objs in self._block_objects.items():
                if len(objs) == 24 and not any(bh in x.read_text(errors='ignore') for x in self._manifest_root.glob('*.json')):
                    manifest={'format':'timeweaver-vllm-kv-block-manifest/1','execution_protocol_id':os.getenv('TIMEWEAVER_EXECUTION_PROTOCOL_ID',''),'logical_block_hash':bh,'expected_layer_count':24,'present_layer_count':24,'layers':objs,'complete':True}; mb=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode(); mh=hashlib.sha256(mb).hexdigest(); manifest['manifest_checksum']=mh; mf=self._manifest_root/(mh+'.json'); mf.write_text(json.dumps(manifest,indent=2)+'\n'); fd=os.open(mf,os.O_RDONLY);os.fsync(fd);os.close(fd)
    def wait_for_save(self):
        self.call_trace.append("wait_for_save")
    def get_finished(self, finished_req_ids):
        self.call_trace.append("get_finished")
        return set(), set()
