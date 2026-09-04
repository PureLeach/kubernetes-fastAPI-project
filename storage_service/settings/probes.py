"""Kubernetes liveness and readiness probes."""

from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING

from fastapi_healthchecks.api.router import HealthcheckRouter, Probe
from fastapi_healthchecks.checks import Check, CheckResult

if TYPE_CHECKING:
    from pathlib import Path


class SnapshotDirWritableCheck(Check):
    """
    Verify the directory holding the snapshot file is writable.

    Persistence is one file on a mounted volume, so a volume that failed to
    mount or came up read-only should take the pod out of the Service.
    """

    name = 'snapshot_dir_writable'

    def __init__(self, snapshot_path: Path) -> None:
        self._directory = snapshot_path.parent

    def _probe(self) -> CheckResult:
        directory = self._directory
        if not directory.is_dir():
            return CheckResult(name=self.name, passed=False, details=f'{directory} is not a directory')
        if not os.access(directory, os.W_OK):
            return CheckResult(name=self.name, passed=False, details=f'{directory} is not writable')
        return CheckResult(name=self.name, passed=True, details=str(directory))

    async def __call__(self) -> CheckResult:
        return await asyncio.to_thread(self._probe)


def build_healthcheck_router(snapshot_path: Path) -> HealthcheckRouter:
    """
    Return the `/probes/*` router for an application.

    Liveness carries no checks: failing it restarts the pod, so anything a
    restart cannot fix belongs in readiness instead.
    """
    return HealthcheckRouter(
        Probe(name='liveness', checks=[]),
        Probe(name='readiness', checks=[SnapshotDirWritableCheck(snapshot_path)]),
    )
