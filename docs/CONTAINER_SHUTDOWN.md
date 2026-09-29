# Container shutdown

The image uses `STOPSIGNAL SIGTERM`; Uvicorn and the service shutdown paths are expected to flush active writers before exit. A full 10,000-event restart-loss measurement remains an operational acceptance check.
