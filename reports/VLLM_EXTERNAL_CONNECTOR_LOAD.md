# External connector load

Source import works without vLLM only to expose the protocol package. A real
vLLM factory load via `kv_connector_module_path` is not executed and does not
pass G0.
