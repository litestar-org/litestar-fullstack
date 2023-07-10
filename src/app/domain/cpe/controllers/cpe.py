"""CPE Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import Controller, post
from litestar.di import Provide

from app.domain.cpe.dependencies import provides_cpe_service
from app.lib import log
from app.domain import urls
from app.domain.cpe.dtos import CreateCpeDTO, CreateCPE, CpeDTO

__all__ = ['CpeController']

if TYPE_CHECKING:
    from litestar.dto.factory import DTOData
    from app.domain.cpe.models import CPE
    from app.domain.cpe.services import CpeService

logger = log.get_logger()


class CpeController(Controller):
    """Account Controller."""

    tags = ["CPES"]
    dependencies = {"cpes_service": Provide(provides_cpe_service)}
    return_dto = CpeDTO

    @post(
        operation_id="CreateCPE",
        name="cpes:create",
        summary="Create a new CPE (customer premises equipment)",
        cache_control=None,
        description="A CPE",
        path=urls.CREATE_CPE,
        dto=CreateCpeDTO,
    )
    async def create_cpe(
        self,
        cpes_service: CpeService,
        data: DTOData[CreateCPE],
    ) -> CPE:
        """Create a new user."""
        obj = data.create_instance()
        db_obj = await cpes_service.create(obj.__dict__)
        return cpes_service.to_dto(db_obj)
