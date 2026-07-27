# Acceptance negative tests

The acceptance runner rejects the tiny model under the acceptance target with
`MODEL_NOT_AUTHORIZED_FOR_ACCEPTANCE`, validates cursor/position consistency,
and rejects token-list checksum mismatch and state-size mismatch. The broader
manifest/runtime mutation matrix remains a follow-up limitation.
