"""CPE Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import Controller, delete, get, post
from litestar.di import Provide
from litestar.params import Dependency, Parameter

from app.domain import urls
from app.domain.cpe.dependencies import provides_cpe_service
from app.domain.cpe.dtos import CpeDTO, CreateCPE, CreateCpeDTO
from app.lib import log

__all__ = ["CpeController"]

if TYPE_CHECKING:
    from litestar.contrib.repository.filters import FilterTypes
    from litestar.dto.factory import DTOData
    from litestar.pagination import OffsetPagination

    from app.domain.cpe.models import CPE
    from app.domain.cpe.services import CpeService

logger = log.get_logger()


class CpeController(Controller):
    """Account Controller."""

    tags = ["CPES"]
    dependencies = {"cpes_service": Provide(provides_cpe_service)}
    return_dto = CpeDTO

    @get(
        operation_id="ListCPEs",
        name="cpes:list",
        summary="List CPEs",
        description="Retrieve the cpe's",
        path=urls.LIST_CPES,
        cache=60,
    )
    async def list_cpes(
        self, cpes_service: CpeService, filters: list[FilterTypes] = Dependency(skip_validation=True)
    ) -> OffsetPagination[CPE]:
        """List users."""
        results, total = await cpes_service.list_and_count(*filters)
        return cpes_service.to_dto(results, total, *filters)

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

    @delete(
        operation_id="DeleteCPE",
        name="CPES:delete",
        path=urls.DELETE_CPE,
        summary="Remove CPE",
        cache_control=None,
        description="Removes a CPE and all associated data from the system.",
        return_dto=None,
    )
    async def delete_cpe(
        self,
        cpes_service: CpeService,
        device_id: str = Parameter(
            title="CPE ID",
            description="The CPE to delete.",
        ),
    ) -> None:
        """Delete a cpe from the system."""
        _ = await cpes_service.delete(device_id)
