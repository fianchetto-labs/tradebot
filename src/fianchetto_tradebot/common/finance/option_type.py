from enum import Enum


class OptionType(str, Enum):
    # make this an enum for PUT or CALL
    PUT = "PUT"
    CALL = "CALL"

    @staticmethod
    def from_str(input:str):
        if input.lower() == "put":
            return OptionType.PUT
        elif input.lower() == "call":
            return OptionType.CALL
        else:
            raise Exception(f"Could not map {input} to option type")
