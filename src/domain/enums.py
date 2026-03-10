from enum import StrEnum


class OrderPaymentStatus(StrEnum):
    UNPAID = 'UNPAID'
    PARTIALLY_PAID = 'PARTIALLY_PAID'
    PAID = 'PAID'


class PaymentType(StrEnum):
    ACQUIRING = 'ACQUIRING'
    CASH = 'CASH'


class PaymentStatus(StrEnum):
    CREATED = 'CREATED'
    PENDING = 'PENDING'
    PAID = 'PAID'
    REFUNDED = 'REFUNDED'
    FAILED = 'FAILED'
