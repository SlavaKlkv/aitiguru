from sqlalchemy import Numeric
from sqlalchemy.orm import mapped_column

from src.domain.constants import MONEY_PRECISION, MONEY_SCALE


def amount_column(*, nullable: bool = False, default=None):
    return mapped_column(
        Numeric(MONEY_PRECISION, MONEY_SCALE),
        nullable=nullable,
        default=default,
    )
