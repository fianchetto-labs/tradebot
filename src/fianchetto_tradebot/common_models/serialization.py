from datetime import date, datetime
from enum import Enum
from typing import TypeVar

from fianchetto_tradebot.common_models.finance.amount import Amount

EnumType = TypeVar("EnumType", bound=Enum)


def serialize_amount_key(value: Amount) -> str:
    return str(value)


def deserialize_amount_key(value) -> Amount:
    if isinstance(value, Amount):
        return value
    return Amount.from_string(value)


def serialize_date_key(value: date) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    return value.isoformat()


def deserialize_date_key(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def serialize_enum_key(value: Enum) -> str:
    return value.value


def deserialize_enum_key(enum_type: type[EnumType], value) -> EnumType:
    if isinstance(value, enum_type):
        return value
    return enum_type(value)
