from dataclasses import dataclass

from litestar.contrib.sqlalchemy.dto import SQLAlchemyDTO
from litestar.dto.factory.stdlib.dataclass import DataclassDTO

from app.domain.cpe.models import CPE
from app.lib import dto

__all__ = [
    "CpeDTO",
    "CreateCPE",
    "CreateCpeDTO",
    "ReadoutCPE",
    "ReadoutCpeDTO",
]


class CpeDTO(SQLAlchemyDTO[CPE]):
    config = dto.config(
        exclude={
            "id",
        },
        max_nested_depth=1,
    )


@dataclass
class CreateCPE:
    device_id: str
    routername: str
    os: str
    mgmt_ip: str
    sec_mgmt_ip: str | None = None


@dataclass
class ReadoutCPE:
    device_id: str


class CreateCpeDTO(DataclassDTO[CreateCPE]):
    """Create CPE."""

    config = dto.config(rename_strategy="lower")


class ReadoutCpeDTO(DataclassDTO[ReadoutCPE]):
    """Readout CPE."""

    config = dto.config(rename_strategy="lower")
