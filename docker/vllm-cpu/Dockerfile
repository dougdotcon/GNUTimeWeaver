FROM ubuntu:24.04

ARG VLLM_TAG=v0.23.0
ARG VLLM_REPO=https://github.com/vllm-project/vllm.git

ENV DEBIAN_FRONTEND=noninteractive \
    VLLM_TARGET_DEVICE=cpu \
    CMAKE_DISABLE_FIND_PACKAGE_CUDA=ON \
    TIMEWEAVER_VLLM_MODE=event_mirror_only \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git build-essential gcc g++ cmake ninja-build pkg-config \
    jq libnuma-dev libtcmalloc-minimal4 python3.12 python3.12-dev python3.12-venv python3-pip \
    && rm -rf /var/lib/apt/lists/*
RUN python3.12 -m venv /opt/timeweaver-venv
ENV PATH=/opt/timeweaver-venv/bin:$PATH
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN git clone --branch "${VLLM_TAG}" --depth 1 "${VLLM_REPO}" /opt/vllm \
    && cd /opt/vllm \
    && test "$(git describe --tags --exact-match)" = "${VLLM_TAG}" \
    && pip install --no-cache-dir -r requirements/build/cpu.txt \
         --extra-index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements/cpu.txt \
         --extra-index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -e . --no-build-isolation
RUN ldconfig -p | grep -q libtcmalloc_minimal.so.4

WORKDIR /workspace/GNUTimeWeaver
ENV PYTHONPATH=/workspace/GNUTimeWeaver/python
COPY python/timeweaver_vllm /workspace/GNUTimeWeaver/python/timeweaver_vllm
COPY config/vllm_connector_v0_3_1.yaml /workspace/GNUTimeWeaver/config/vllm_connector_v0_3_1.yaml
COPY tools/vllm_g0_g1.py /workspace/GNUTimeWeaver/tools/vllm_g0_g1.py
COPY tools/vllm_engine.py /workspace/GNUTimeWeaver/tools/vllm_engine.py
COPY tools/check_vllm_engine_ready.py /workspace/GNUTimeWeaver/tools/check_vllm_engine_ready.py
COPY tools/connector_preflight.py /workspace/GNUTimeWeaver/tools/connector_preflight.py
ENTRYPOINT ["python", "tools/vllm_g0_g1.py"]
