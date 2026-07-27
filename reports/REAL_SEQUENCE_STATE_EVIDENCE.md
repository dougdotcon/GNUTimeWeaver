# Sequence state evidence

The smoke run serialized and restored 886,440 bytes through the official
sequence-state size/get/set APIs. Prefix positions restored as 0..127 in a new
process. Checkpoint PID 8560 and restore PID 8116 were distinct.
