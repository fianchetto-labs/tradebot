from enum import Enum

class ServiceKey(str, Enum):
    ORDERS = "orders"
    QUOTES = "quotes"
    MOEX = "moex"
    TRIDENT = "trident"
    HELM = "helm"
