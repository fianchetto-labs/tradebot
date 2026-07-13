from pydantic import field_serializer, field_validator

from fianchetto_tradebot.common_models.api.request import Request
from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.common_models.serialization import deserialize_enum_key, serialize_enum_key


class ListManagedExecutionsRequest(Request):
    accounts: dict[Brokerage, str]
    # TODO: Filter for active vs. finished, cancelled, etc.

    @field_serializer("accounts", when_used="always")
    def serialize_accounts(self, accounts: dict[Brokerage, str]):
        return {serialize_enum_key(brokerage): account_id for brokerage, account_id in accounts.items()}

    @field_validator("accounts", mode="before")
    @classmethod
    def deserialize_accounts(cls, value):
        if isinstance(value, dict):
            return {
                deserialize_enum_key(Brokerage, brokerage): account_id
                for brokerage, account_id in value.items()
            }
        return value
