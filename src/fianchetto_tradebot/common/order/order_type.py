from enum import Enum


class OrderType(Enum):
    EQ = "EQ"
    OPTN = "OPTN"
    SPREADS = "SPREADS"
    BUY_WRITES = "BUY_WRITES"
    BUTTERFLY = "BUTTERFLY"
    IRON_BUTTERFLY = "IRON_BUTTERFLY"
    CONDOR = "CONDOR"
    IRON_CONDOR = "IRON_CONDOR"
    MF = "MF"
    MMF = "MMF"

    def __str__(self):
        return self.name  # Ensures string conversion returns the name