from sqlalchemy import Numeric
from sqlalchemy.orm import mapped_column

from src.domain.constants import AMOUNT_PRECISION, AMOUNT_SCALE


def amount_column(
    *, nullable: bool = False, default=None, server_default=None
):
    return mapped_column(
        Numeric(AMOUNT_PRECISION, AMOUNT_SCALE),
        nullable=nullable,
        default=default,
        server_default=server_default,
    )
