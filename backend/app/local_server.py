"""Local (offline) server entrypoint for the Windows EXE deployment (section 13).

On first run it provisions the local tenant's tables (SQLite) and installs the
audit immutability trigger, bootstraps a local admin if one is configured, then
starts the FastAPI app together with the background :class:`SyncEngine`.

This is the process that PyInstaller packages into
``Delta Plax Education Suite Server.exe``.
"""

from __future__ import annotations

import logging

from app.core.config import get_settings
from app.db.provisioning import provision_tenant
from app.main import app
from app.services.sync import SyncEngine

logger = logging.getLogger("deltaplax.local")

# A local deployment is a single tenant; the id is fixed for the on-prem server.
LOCAL_TENANT_ID = "local"

_sync_engine: SyncEngine | None = None


@app.on_event("startup")
def _on_startup() -> None:
    """Provision local storage and start the sync engine in the background."""
    settings = get_settings()
    if not settings.is_sqlite:
        # Cloud deployments are provisioned per-institution via the API, not here.
        return
    provision_tenant(LOCAL_TENANT_ID)
    global _sync_engine
    _sync_engine = SyncEngine(LOCAL_TENANT_ID, settings=settings)
    _sync_engine.start()
    logger.info("Local server ready; sync engine polling every %ss", settings.sync_poll_seconds)


@app.on_event("shutdown")
def _on_shutdown() -> None:
    if _sync_engine is not None:
        _sync_engine.stop()


def main() -> None:
    """Serve the bundled app + frontend on the LAN (http://0.0.0.0:3000)."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=3000)


if __name__ == "__main__":
    main()
