# vLLM Block Connector v0.3 preregistration

Protocol ID: `timeweaver-vllm-block-connector-v0.3:5d8e9f3f16e89b1d8042fe5328f531a6080ee51600193b0e678bdc808ad5083d`

The target runtime is vLLM v0.26.0, commit prefix `568afb3`, loaded externally
on native Linux or WSL2. The connector API is experimental `KVConnectorBase_V1`;
persistent identity uses canonical `sha256_cbor`, never local runtime block IDs.
CPU is the initial profile, with hybrid cache disabled until explicitly tested.

Current host is native Windows with no WSL distribution, Python has neither
PyTorch nor vLLM, and no Transformers/safetensors model is provisioned.
Therefore this protocol is preregistered but not executable here.
