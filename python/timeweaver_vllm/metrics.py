from dataclasses import dataclass
@dataclass
class RestoreMetrics:
    external_matched_tokens: int = 0
    loaded_full_block_tokens: int = 0
    prefill_tokens_executed_for_loaded_blocks: int = 0
