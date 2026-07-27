# v0.23.0 API compatibility

| Component | v0.3 hypothesis | v0.23.0 | Change | Test |
|---|---|---|---|---|
| connector.py | presumed base | real `KVConnectorBase_V1` | exact abstract signatures added | source audit |
| scheduler_connector.py | split role | supported | inherits main connector | import only |
| worker_connector.py | split role | supported | inherits main connector | import only |
| block_identity.py | canonical identity | conceptually valid | await real event fields | unit |
| block_store.py | immutable store | out of G1 scope | no payload use | unit |
| events.py | sequence mirror | compatible concept | add real decoder in G1 | unit |
| daemon_client.py | Unix socket | unavailable on host | defer to Linux | not run |

The event-mirror connector implements the v0.23.0 scheduler and worker abstract
method signatures and always returns zero external matches.
