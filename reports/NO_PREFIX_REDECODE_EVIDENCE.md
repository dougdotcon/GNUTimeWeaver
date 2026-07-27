# Prefix redecode evidence

Smoke result: `prefix_tokens_decoded_after_restore == 0` for restore and both
branches. The checkpoint stores the greedy pending token separately so
continuation can decode new generated work without replaying a prefix token.
