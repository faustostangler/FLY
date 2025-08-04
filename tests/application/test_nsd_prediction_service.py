from datetime import datetime, timedelta
from unittest.mock import MagicMock

from application.services.nsd_prediction_service import _find_next_probable_nsd
from domain.dto.nsd_dto import NsdDTO
from domain.ports import NSDRepositoryPort


def test_find_next_probable_nsd_returns_sequence():
    repo = MagicMock(spec=NSDRepositoryPort)
    now = datetime.utcnow()
    start = now - timedelta(days=15)

    items = []
    for i in range(10):
        items.append(
            NsdDTO(
                nsd=str(i + 1),
                company_name="Comp",
                quarter=None,
                version=None,
                nsd_type=None,
                dri=None,
                auditor=None,
                responsible_auditor=None,
                protocol=None,
                sent_date=start + timedelta(days=i),
                reason=None,
            )
        )
    repo.get_all.return_value = items

    result = _find_next_probable_nsd(
        repository=repo,
        window_days=20,
        safety_factor=1.0,
    )

    max_date = start + timedelta(days=9)
    min_date = start
    days_span = (max_date - min_date).days
    daily_avg = len(items) / days_span
    days_since_last = (now - max_date).days
    expected_count = int(daily_avg * days_since_last * 1.0)
    expected = [len(items) + i for i in range(1, expected_count + 1)]

    assert result == expected


def test_find_next_probable_nsd_empty():
    repo = MagicMock(spec=NSDRepositoryPort)
    repo.get_all.return_value = []

    result = _find_next_probable_nsd(repo)
    assert result == []
