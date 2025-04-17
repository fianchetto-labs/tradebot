from enum import Enum

class ServiceKey(str, Enum):
    OEX = "oex"
    QUOTES = "quotes"
    TRIDENT = "trident"
    HELM = "helm"
