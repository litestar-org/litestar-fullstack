from sqlalchemy.orm import Mapped

from app.lib.db import orm

__all__ = ["CPE"]


class CPE(orm.TimestampedDatabaseModel):
    device_id: Mapped[str]  # cap_id in business term
    routername: Mapped[str]
    os: Mapped[str]
    mgmt_ip: Mapped[str]
    sec_mgmt_ip: Mapped[str | None]
