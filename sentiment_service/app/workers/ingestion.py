from __future__ import annotations

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class IngestionWorker:
    def __init__(self, pipeline, interval_seconds: int):
        self.pipeline = pipeline
        self.interval_seconds = max(5, interval_seconds)
        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()

    async def start(self) -> None:
        if not self._task:
            self._task = asyncio.create_task(self._run(), name="news-ingestion-worker")

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run(self) -> None:
        while not self._stop.is_set():
            try:
                await self.pipeline.run_once(list(self.pipeline.entity_extractor.company_mapping.keys()))
            except Exception:
                logger.exception("NEWS_WORKER_CYCLE_FAILED")
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self.interval_seconds)
            except asyncio.TimeoutError:
                pass

