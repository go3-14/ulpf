# T1.5 validation investigation

## Method

`scripts/diagnose_validation.py` loads the bundled OCSF 1.9.0 class schema directly with `Draft202012Validator`; it does not remove or rewrite `additionalProperties` rules. It processes the first non-empty line of `samples/cisco_asa_syslog.log` through the real pipeline and prints every failing JSON pointer and message.

## Evidence

Before the fix, validating the real normalized event against the intact schema produced:

```text
/: Additional properties are not allowed ('mapping_version' was unexpected)
```

The suspected fields were not the cause. The official class schema contains `metadata.labels`, `metadata.original_time`, `metadata.logged_time`, and `unmapped`; `unmapped` resolves to the schema's object definition. The actual non-OCSF field was the engine-added top-level `mapping_version`.

The fix removes that top-level field from normalized OCSF bodies. Mapping version remains mapping configuration data and will belong in provenance/index metadata in the later storage phase.

After the fix:

```text
event_id: 65d2a6e3-6278-4a36-b9a4-13fd109afff0
top_level_keys: ['activity_id', 'category_uid', 'class_uid', 'connection_info', 'dst_endpoint', 'metadata', 'severity_id', 'src_endpoint', 'time', 'type_uid', 'unmapped']
VALID: no schema errors
```

`schema/validate.py` no longer contains the blanket `_strip_additional_properties()` behavior. `additionalProperties: false` remains intact throughout validation.

## Regression proof

`tests/test_phase0_checkpoint.py::test_phase0_rejects_misspelled_endpoint_property` supplies a valid `src_endpoint.ip` plus the misspelled `src_endpoint.ipp` and asserts validation failure. This proves strict additional-property checking remains active.
