# Phase 0 performance baseline

Profiles were captured before optimization with validation enabled, exactly 2,000 events, and a fresh storage directory per run.

## Windows

Benchmark result: 2,000 submitted, 2,000 ingested, 14.464 s, 138.3 events/s, 2.51 MB.

Top cumulative time:

```text
5868972 calls in 14.472 s
pipeline.py:39(process)                         14.454 s cumulative
writer.py:57(write)                              8.026 s
writer.py:34(_get_handle_and_lock)               5.545 s
normalized_store.py:14(store_normalized)         4.095 s
raw_store.py:9(store_raw)                        3.960 s
validate.py:74(validate_event)                   3.894 s
pathlib.py:981(resolve)                          3.883 s
validators.py:349(iter_errors)                   3.863 s
validators.py:396(descend)                      3.753 s
_keywords.py:290(properties)                    3.730 s
_keywords.py:274(ref)                           3.037 s
pathlib.py:1111(mkdir)                           2.803 s
ntpath.py:633(realpath)                          2.774 s
nt._getfinalpathname                           2.469 s
pathlib.py:1008(stat)                            2.230 s
nt.stat                                         2.196 s
nt.mkdir                                        1.917 s
index.py:35(add_index)                           1.577 s
writer.py:25(_get_base_dir)                      1.494 s
_keywords.py:337(anyOf)                         1.020 s
validators.py:339(evolve)                       0.989 s
```

Top internal time:

```text
nt._getfinalpathname                           2.469 s
nt.stat                                         2.064 s
nt.mkdir                                        1.834 s
validators.py:396(descend)                      0.556 s
io.open                                          0.433 s
validators.py:339(evolve)                       0.430 s
_keywords.py:290(properties)                    0.169 s
encoder.py:205(iterencode)                      0.132 s
writer.py:34(_get_handle_and_lock)              0.122 s
_keywords.py:282(type)                          0.124 s
```

## Linux container

Top cumulative time:

```text
6049306 calls in 41.645 s
pipeline.py:39(process)                         41.558 s cumulative
writer.py:57(write)                              26.392 s
pathlib.py:981(resolve)                          18.176 s
writer.py:34(_get_handle_and_lock)              15.844 s
posixpath.py:409(realpath)                       15.353 s
posixpath.py:418(_joinrealpath)                  15.178 s
posix.lstat                                      14.261 s
normalized_store.py:14(store_normalized)         13.340 s
raw_store.py:9(store_raw)                        13.088 s
index.py:35(add_index)                           10.195 s
pathlib.py:1008(stat)                             9.861 s
posix.stat                                        9.809 s
pathlib.py:1111(mkdir)                            6.720 s
pathlib.py:1245(is_dir)                           4.809 s
validate.py:74(validate_event)                    3.899 s
io.open                                           3.880 s
validators.py:349(iter_errors)                    3.865 s
validators.py:396(descend)                        3.748 s
_keywords.py:290(properties)                     3.696 s
```

Top internal time:

```text
posix.lstat                                      14.261 s
posix.stat                                        9.660 s
io.open                                           3.850 s
file close (__exit__)                             2.515 s
posix.mkdir                                        1.762 s
TextIOWrapper.flush                                1.333 s
validators.py:396(descend)                        0.544 s
posixpath.py:418(_joinrealpath)                    0.412 s
encoder.py:205(iterencode)                        0.169 s
writer.py:34(_get_handle_and_lock)                0.169 s
```

## Findings

1. Filesystem path resolution and metadata dominate: `storage/writer.py:25-47` repeatedly resolves, stats, creates, and scans partition paths; this appears as `pathlib.resolve`, `realpath`, `stat`, `mkdir`, `lstat`, and `is_dir`.
2. Every event calls `PartitionedNDJSONWriter.write` (`storage/writer.py:57-72`) for raw and normalized data and flushes each record at line 67.
3. The in-memory NDJSON index writes and opens the index file per event (`storage/index.py:35-42`), contributing through `add_index` and `io.open`.
4. Full JSON-schema validation is material (`schema/validate.py:74-89`, `jsonschema.validators` traversal), but is not the largest cost in this baseline.
5. JSON serialization is measurable but smaller (`storage/writer.py:58-59`, `encoder.py:205`); regex compilation and hot-path logging do not appear in the top costs because mappings/regexes are loaded once and the benchmark emits no per-event log records.

No optimization was made in T0.4.
