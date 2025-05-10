from enum import Enum


class Action(str, Enum):
    BUY_OPEN = "BUY_OPEN"
    SELL_OPEN = "SELL_OPEN"
    BUY_CLOSE = "BUY_CLOSE"
    SELL_CLOSE = "SELL_CLOSE"
    BUY = "BUY"
    SELL = "SELL"

    @staticmethod
    def is_long(action):
        return action in LONGS

    @staticmethod
    def is_short(action):
        return not Action.is_long(action)

SHORTS = {Action.SELL, Action.SELL_OPEN, Action.SELL_CLOSE}
LONGS = {Action.BUY, Action.BUY_OPEN, Action.BUY_CLOSE}