from dataclasses import dataclass
from .errors import CompatibilityError

@dataclass(frozen=True)
class KVEvent:
    sequence_number: int
    event_type: str
    block_hashes: tuple
    parent_block_hash: str | None = None

class EventMirror:
    def __init__(self):
        self.last_sequence = 0
        self.events = []
        self.blocks = {}
    def consume(self, event: KVEvent):
        if event.sequence_number <= self.last_sequence:
            if event.sequence_number == self.last_sequence:
                return "duplicate"
            raise CompatibilityError("EVENT_SEQUENCE_REGRESSION")
        if event.sequence_number != self.last_sequence + 1:
            raise CompatibilityError("EVENT_GAP_REPLAY_REQUIRED")
        self.last_sequence = event.sequence_number
        self.events.append(event)
        for block in event.block_hashes:
            self.blocks[block] = event.event_type
        return "accepted"
