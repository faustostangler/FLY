# application/usecases/sync_nsd.py (semântica mantida, apenas léxico)
from domain.events.events import NSDReady

class SyncNSDUseCase:
    def __init__(self, nsd_repo, outbox_repo, clock, id_gen):
        self._nsd_repo = nsd_repo
        self._outbox = outbox_repo
        self._clock = clock
        self._id_gen = id_gen

    def run(self, nsd_payload) -> None:
        now = self._clock.now()
        nsd = self._nsd_repo.insert_or_update(nsd_payload, now)
        evt = NSDReady(nsd_id=nsd.id, version_hash=nsd.version_hash, occurred_at=now, correlation_id=self._id_gen.create_id(12))
        self._outbox.add(topic="NSDReady", event_obj=evt, occurred_at=now)
        # commit é responsabilidade da UoW quem chama este caso de uso
from __future__ import annotations

from domain.events.events import NSDReady


class SyncNSDUseCase:
    def __init__(self, nsd_repo, outbox_repo, clock, id_gen):
        self._nsd_repo = nsd_repo
        self._outbox = outbox_repo
        self._clock = clock
        self._id_gen = id_gen

    def run(self, nsd_payload) -> None:
        now = self._clock.now()
        nsd = self._nsd_repo.insert_or_update(nsd_payload, now)
        evt = NSDReady(
            nsd_id=nsd.id,
            version_hash=nsd.version_hash,
            occurred_at=now,
            correlation_id=self._id_gen.create_id(12),
        )
        self._outbox.add(topic="NSDReady", event_obj=evt, occurred_at=now)
        # commit é responsabilidade da UoW de quem chama este caso de uso
