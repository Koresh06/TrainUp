from dataclasses import dataclass

from src.domain.exception.base import DomainError


@dataclass
class PackageNotFoundException(DomainError):
    package_id: int

    @property
    def message(self) -> str:
        return f"Абонемент {self.package_id} не найден"


@dataclass
class PackageNotChargeableException(DomainError):
    package_id: int

    @property
    def message(self) -> str:
        return f"С абонемента {self.package_id} нельзя списать занятие"
