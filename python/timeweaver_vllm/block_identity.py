import hashlib, json
from dataclasses import dataclass

@dataclass(frozen=True)
class TimeWeaverKVBlockKey:
    fields: dict
    def canonical_bytes(self) -> bytes:
        return json.dumps(self.fields, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    def digest(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()
    @classmethod
    def from_event(cls, **fields):
        return cls(dict(fields))
