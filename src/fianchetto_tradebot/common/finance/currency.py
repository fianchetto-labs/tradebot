from enum import Enum


class Currency(str, Enum):
    US_DOLLARS = "usd"
    CANADIAN_DOLLARS = "cad"
    EURO = "eur"
    MEXICAN_PESO = "mep"