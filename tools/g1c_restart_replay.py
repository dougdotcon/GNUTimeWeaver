import json,os,time
def main():
 import zmq
 out=os.environ['TIMEWEAVER_G1C_RESULTS'];ctx=zmq.Context();s=ctx.socket(zmq.DEALER);s.setsockopt(zmq.IDENTITY,b'g1c-restarted-mirror');s.connect('tcp://vllm-engine:5558');s.send_multipart([b'',(0).to_bytes(8,'big')]); seqs=[];end=False
 while True:
  frames=s.recv_multipart(); raw=frames[-2:];
  if raw[0]==b'\xff'*8: end=True;break
  seqs.append(int.from_bytes(raw[0],'big'))
 open(out+'/restart-replay.json','w').write(json.dumps({'request_start':0,'returned_sequences':seqs,'END_SEQ_observed':end,'restarted_mirror_id':'g1c-restarted-mirror'},indent=2)+'\n')
if __name__=='__main__':main()
