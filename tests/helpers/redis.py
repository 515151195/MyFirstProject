from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EnqueuedJob:
    function: str
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)


class FakeArqRedis:
    """Small ARQ-compatible recorder used by API and worker tests."""

    def __init__(self) -> None:
        self.jobs: list[EnqueuedJob] = []

    async def enqueue_job(
        self,
        function: str,
        *args: Any,
        **kwargs: Any,
    ) -> EnqueuedJob:
        job = EnqueuedJob(function=function, args=args, kwargs=kwargs)
        self.jobs.append(job)
        return job

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        return None

    def jobs_for(self, function: str) -> list[EnqueuedJob]:
        return [job for job in self.jobs if job.function == function]

    def clear(self) -> None:
        self.jobs.clear()


def make_worker_context(redis: FakeArqRedis | None = None) -> dict[str, FakeArqRedis]:
    return {"arq_redis": redis or FakeArqRedis()}


def patch_redis_pool(monkeypatch: Any, redis: FakeArqRedis | None = None) -> FakeArqRedis:
    fake_redis = redis or FakeArqRedis()

    async def fake_get_redis_pool() -> FakeArqRedis:
        return fake_redis

    import core.queue as queue_module
    import services.outbox_service as outbox_module

    monkeypatch.setattr(queue_module, "get_redis_pool", fake_get_redis_pool)
    monkeypatch.setattr(outbox_module, "get_redis_pool", fake_get_redis_pool)
    return fake_redis
