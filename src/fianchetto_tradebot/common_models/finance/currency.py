from enum import Enum


class Currency(str, Enum):
    US_DOLLARS = "USD"
    CANADIAN_DOLLARS = "CAD"
    EURO = "EUR"
    MEXICAN_PESO = "MEP"

    def __str__(self):
        return self.value