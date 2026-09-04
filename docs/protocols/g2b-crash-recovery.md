# G2-B3 crash and staging recovery

Crash at object, manifest and queue boundaries. On restart enumerate staging, reconcile with the journal, validate checksums and quarantine incomplete material; never auto-promote staging. Preserve valid committed orphans and report them.
