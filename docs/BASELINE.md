# Phase 0 baseline

## Environment

- Repository branch: `master`
- Python: `3.11.15` (`.venv`)
- Docker server: `29.5.3`
- Requirements installed from `requirements-dev.txt`.

## Raw pytest result

Command: `.venv\Scripts\python.exe -m pytest -q`

The baseline command completed with:

```text
19 passed, 1 warning, 10 errors in 9.45s
```

All ten errors occur during `tmp_path` fixture setup. Pytest cannot scan the host directory `C:\Users\Gopi\AppData\Local\Temp\pytest-of-Gopi` because it contains an inaccessible entry (`PermissionError: [WinError 5]`). No repository pytest configuration for `pytest_tmp` or `basetemp` exists. This is recorded for T0.2/A1; no `--basetemp` workaround was used.

Warning:

```text
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

## Defect verification

| Defect | Result | Evidence |
|---|---|---|
| D1 | Present | `schema/normalize.py` adds a field to `consumed` before skipping empty values. |
| D2 | Present | `schema/transforms.py` leaves yearless values at year 1900 except for the `current` assumption. |
| D3 | Present | `parse_time_ms` always attaches UTC and does not read `time.timezone`. |
| D4 | Present | `to_enum` lowercases only the input, not mapping keys. |
| D5 | Present | The syslog envelope regex can consume a PRI-only `date=...` token as hostname. |
| D6 | Present | `schema/validate.py` strips all `additionalProperties: false` and returns early for non-4001 classes. |
| D7 | Present | `ingest/pipeline.py` creates IDs with `uuid.uuid4()`. |
| D8 | Present | `storage/index.py` and `storage/normalized_store.py` use unbounded module-level dictionaries. |
| D9 | Present | Normalized-store search scans NDJSON partitions linearly. |
| D10 | Present | Vendor-specific ASA/action behavior exists in `parsers/syslog.py`. |
| D11 | Present | Pipeline failures go to `storage.failed` instead of producing a fallback event. |
| D12 | Not yet verified | Docker is available now; the build/test evidence is collected in T0.3. |

## Code/status differences from the status report

- The repository has no `pytest.ini`, `pyproject.toml`, `setup.cfg`, `tox.ini`, or `conftest.py` configuring `pytest_tmp`; the current failure is caused by the host temp directory ACL.
- The checked-in Dockerfile is single-stage and has no `test` target; T0.3 adds the required test stage.
- The current local tree contains tracked runtime data and bytecode; T0.2 handles the hygiene cleanup.
- `tui/app.py` is a Textual/httpx client of the FastAPI service, but it also writes directly to `spool/` and launches the benchmark subprocess. Addendum A5 defers its API-only correction to the later TUI scope.

## T0.3 Docker evidence

Build command:

```text
docker build --target test -t ulpf-test .
...
#12 naming to docker.io/library/ulpf-test:latest
#12 DONE
```

Container test-stage command and raw result:

```text
docker run --rm ulpf-test python -m pytest -q
.............................                                            [100%]
29 passed, 1 warning in 4.66s
```

Isolated processing command:

```text
docker run --rm --network none -v <repo>\samples:/samples:ro -v <temp>:/data \
  -e ULPF_STORAGE_DIR=/data/storage -e ULPF_SPOOL_DIR=/data/spool \
  ulpf-test python -m cli.main process /samples/cisco_asa_syslog.log
```

Result:

```text
PROCESSED: 26a1a644-46de-4822-b1d8-50d4b576eafc
PROCESSED: ab312d12-cd55-42b9-8b04-8934860d1d08
PROCESSED: eaa5d6b8-4645-41d8-9176-60c1d5e89e0a
PROCESSED: 0eed8efa-2dcb-4837-8551-b3bff00f3502
PROCESSED: cd70370a-aa1a-465c-8d76-9bca7b1f6388
PROCESSED: 6c1c2784-8c3c-4759-84ac-2bbe7a57c6be
FAILED: malformed ASA line without a syslog envelope

Summary: 6 processed, 1 failed.
```
