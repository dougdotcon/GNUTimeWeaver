# Acceptance replay versus restore benchmark

Five repetitions were run per prefix length with the same CPU/build. The
recorded process times include model load. Restore excludes neither model load
nor context creation; therefore wall-clock speedup is not claimed. The primary
benefit is avoided prefill tokens: 512, 1024 and 2048 respectively.
