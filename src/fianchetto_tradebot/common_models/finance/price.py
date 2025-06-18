from statistics import mean
from typing import Optional

from pydantic import BaseModel, computed_field, field_validator


class Price(BaseModel):
    bid: float
    ask: float
    last: Optional[float] = None

    @field_validator('bid', 'ask', mode='before')
    @classmethod
    def round_to_two_decimals(cls, value: float) -> float:
        return round(value, 2)

    @computed_field
    @property
    def mark(self)->float:
        return round(mean([self.bid, self.ask]), 2)

    def __repr__(self):
        return f"{self.mark:.2f}\t|\t{self.bid:.2f}\t|\t{self.ask:.2f}\t"

    def __str__(self):
        return f"{self.mark:.2f}\t|\t{self.bid:.2f}\t|\t{self.ask:.2f}\t"

    def copy_of(self):
        if hasattr(self, 'last'):
            return Price(bid=self.bid, ask=self.ask, last=self.last)
        return Price(bid=self.bid, ask=self.ask)

    def __add__(self, other):
        return Price(bid=self.bid + other.bid, ask=self.ask + other.ask)

    def __sub__(self, other):
        return Price(bid=self.bid - other.ask, ask=self.ask - other.bid)

    def __mul__(self, factor):
        return Price(bid=self.bid * factor, ask=self.ask * factor)

    def __truediv__(self, divisor: float):
        if divisor == 0:
            raise ZeroDivisionError("Cannot divide Price by zero.")

        return Price(bid=self.bid / divisor, ask=self.ask / divisor)