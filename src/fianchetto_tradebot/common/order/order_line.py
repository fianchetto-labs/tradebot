
from pydantic import BaseModel, field_validator, field_serializer

from fianchetto_tradebot.common.finance.equity import Equity
from fianchetto_tradebot.common.finance.option import Option
from fianchetto_tradebot.common.order.action import Action
from fianchetto_tradebot.common.finance.tradable import Tradable

QUANTITY_FILLED_NOT_SPECIFIED = -1

class OrderLine(BaseModel):
    tradable: Tradable
    action: Action
    quantity: int
    quantity_filled: int = QUANTITY_FILLED_NOT_SPECIFIED

    class Config:
        use_enum_values = True

    @field_serializer('tradable')
    def serialize_tradable(self, value: Tradable, _info):
        return {
            "__type__": value.__class__.__name__,
            **value.model_dump()
        }


    #@field_serializer("action")
    #def serialize_price_type(self, v: Action, _info):
    #    return v.name

    # --- VALIDATOR: extract class name and dispatch
    @field_validator('tradable', mode='before')
    @classmethod
    def deserialize_tradable(cls, value):
        if isinstance(value, Tradable):  # already parsed
            return value
        type_ = value.pop("__type__", None)
        if type_ == "Option":
            return Option.model_validate(value)
        elif type_ == "Equity":
            return Equity.model_validate(value)
        else:
            raise ValueError(f"Unknown Tradable type: {type_}")


    @staticmethod
    def __validate__(quantity, action, tradable):
        # Factored this out of __init__...TODO: Use Pydantic to implement validation
        if not quantity or type(quantity) is not int or quantity < 1:
            raise Exception(f"Invalid value for quantity: {quantity}")

        if not action:
            raise Exception(f"Action required")

        if not tradable:
            raise Exception(f"Tradable required")



    def __str__(self):
        return f"{self.action}: {self.quantity} x {self.tradable}"

    def __hash__(self):
        return hash((self.tradable, self.action, self.quantity, self.quantity_filled))

    def __eq__(self, other):
        if self.tradable != other.tradable:
            return False
        if self.action != other.action:
            return False
        if self.quantity != other.quantity:
            return False
        if self.quantity_filled:
            if self.quantity_filled != other.quantity_filled:
                return False

        return True