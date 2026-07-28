#!/usr/bin/env python3
"""Real vLLM KV-event PUB subscriber for the bounded G1-A/W0 gate."""
from __future__ import annotations
import hashlib, json, os, struct, time
from datetime import datetime, timezone
from pathlib import Path

def now(): return datetime.now(timezone.utc).isoformat()
def main():
    import msgspec, zmq
    from vllm.distributed.kv_events import KVEventBatch, BlockStored
    results = Path(os.environ.get("TIMEWEAVER_RESULTS", "/results")); results.mkdir(parents=True, exist_ok=True)
    run_id = os.environ.get("TIMEWEAVER_RUN_ID", "unidentified")
    engine_id = os.environ.get("TIMEWEAVER_ENGINE_ID", f"timeweaver-v031-{run_id}")
    topic = os.environ.get("TIMEWEAVER_KV_TOPIC", "timeweaver-kv-v031").encode()
    endpoint = os.environ.get("TIMEWEAVER_KV_ENDPOINT", "tcp://vllm-engine:5557")
    trace_bin = results / "vllm_v031_w0_wire_trace.bin"; trace_json = results / "vllm_v031_w0_wire_trace.jsonl"
    ready_dir = results / "readiness"; ready_dir.mkdir(exist_ok=True)
    ready = ready_dir / "event-mirror.json"
    ctx = zmq.Context.instance(); sock = ctx.socket(zmq.SUB); sock.setsockopt(zmq.RCVHWM, 10000); sock.connect(endpoint); sock.setsockopt(zmq.SUBSCRIBE, topic)
    started = now(); ready.write_text(json.dumps({"pid": os.getpid(), "consumer_id": f"mirror-{os.getpid()}", "configured_topic": topic.decode(), "pub_endpoint": endpoint, "replay_endpoint": "tcp://vllm-engine:5558", "subscriber_socket_created": True, "subscription_installed": True, "subscriber_configured": True, "publisher_observed": False, "first_event_received": False, "started_at": started, "ready_at": now(), "engine_id": engine_id}, indent=2)+"\n")
    decoder = msgspec.msgpack.Decoder(KVEventBatch); records=[]; blocks=[]; last=time.monotonic(); deadline=last+float(os.getenv("TIMEWEAVER_G1A_TIMEOUT", "180"))
    with trace_bin.open("wb") as raw, trace_json.open("w", encoding="utf-8") as jf:
        while time.monotonic() < deadline:
            events = dict(sock.poll(1000) and [("x", sock.recv_multipart())] or []).get("x")
            if not events: continue
            received=now(); frame_count=len(events); t, seqb, payload = (events+[b"",b"",b""])[:3]
            seq=int.from_bytes(seqb,"big") if len(seqb)==8 else None
            raw.write(struct.pack("!I", frame_count))
            for frame in events: raw.write(struct.pack("!I", len(frame))+frame)
            rec={"data_origin":"real_vllm_zmq","run_id":run_id,"engine_id":engine_id,"received_at":received,"frame_count":frame_count,"topic_utf8":t.decode(errors="replace"),"topic_hex":t.hex(),"sequence":seq,"sequence_hex":seqb.hex(),"payload_size":len(payload),"payload_sha256":hashlib.sha256(payload).hexdigest(),"raw_message_sha256":hashlib.sha256(b"".join(events)).hexdigest(),"decode_status":"failed"}
            try:
                batch=decoder.decode(payload); rec["decode_status"]="ok"; rec["decoded_type"]="vllm.distributed.kv_events.KVEventBatch"; rec["event_count"]=len(batch.events)
                for idx,event in enumerate(batch.events):
                    if isinstance(event, BlockStored):
                        blocks.append({"sequence":seq,"event_index":idx,"block_hashes":list(event.block_hashes),"parent_block_hash":event.parent_block_hash,"token_ids":list(event.token_ids),"block_size":event.block_size,"medium":event.medium,"lora_name":event.lora_name,"extra_keys":event.extra_keys,"group_idx":event.group_idx})
                rec["block_stored_count"]=sum(1 for e in batch.events if isinstance(e, BlockStored))
            except Exception as exc: rec["decode_error"]=repr(exc)
            jf.write(json.dumps(rec)+"\n"); jf.flush(); raw.flush(); records.append(rec); last=time.monotonic()
            if blocks and time.monotonic()-last < 0.1: pass
            # For G1-B keep the subscriber alive across W0/W1/W2/W3. The
            # bounded run ends on the preregistered deadline.
    ready_data=json.loads(ready.read_text()); ready_data.update({"publisher_observed": bool(records),"first_event_received": bool(records),"last_sequence": records[-1]["sequence"] if records else None,"total_event_batches":len(records),"total_decoded_events":sum(r.get("event_count",0) for r in records),"total_block_stored":len(blocks),"finished_at":now()}); ready.write_text(json.dumps(ready_data,indent=2)+"\n")
    (results/"g1a-blockstored.json").write_text(json.dumps({"engine_id":engine_id,"blocks":blocks,"records":records},indent=2)+"\n")
    return 0 if blocks else 2
if __name__ == "__main__": raise SystemExit(main())
