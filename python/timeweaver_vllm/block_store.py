import hashlib, json, os, tempfile
from pathlib import Path
from .errors import CompatibilityError

class ImmutableBlockStore:
    """Content-addressed complete-only block store; no pickle or tensor loading."""
    def __init__(self, workspace):
        self.root = Path(workspace).resolve() / "kv3"
        self.objects = self.root / "objects"
        self.manifests = self.root / "manifests"
        self.staging = self.root / "staging"
        for p in (self.objects, self.manifests, self.staging):
            p.mkdir(parents=True, exist_ok=True)
    def put(self, key: str, payload: bytes, manifest: dict) -> str:
        digest = hashlib.sha256(payload).hexdigest()
        if manifest.get("timeweaver_block_key") != key or not manifest.get("complete"):
            raise CompatibilityError("INCOMPLETE_BLOCK_MANIFEST")
        target = self.objects / digest[:2] / key
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.staging, prefix="block-")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(payload); f.flush(); os.fsync(f.fileno())
            os.replace(tmp, target)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)
        m = dict(manifest, payload_hash=digest, payload_size=len(payload))
        mpath = self.manifests / f"{key}.json"
        mpath.write_text(json.dumps(m, sort_keys=True), encoding="utf-8")
        return digest
