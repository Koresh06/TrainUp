from datetime import date, timedelta

import pytest

from src.domain.entities.client_package import ClientPackage
from src.domain.enums.package import PackageStatus
from src.domain.exception.package import PackageNotChargeableException

TODAY = date(2026, 10, 21)


def make(**kwargs) -> ClientPackage:
    return ClientPackage(trainer_id=1, client_id=1, title="2 занятия", sessions_total=2, **kwargs)


def test_charge_until_finished_and_refund() -> None:
    package = make()
    package.charge(TODAY)
    package.charge(TODAY)
    assert package.status == PackageStatus.FINISHED and package.remaining == 0
    with pytest.raises(PackageNotChargeableException):
        package.charge(TODAY)
    package.refund()
    assert package.status == PackageStatus.ACTIVE and package.remaining == 1


def test_expired_package_is_not_chargeable() -> None:
    package = make(valid_until=TODAY - timedelta(days=1))
    assert package.is_expired(TODAY) and not package.can_charge(TODAY)

