from enum import Enum

EUROPEAN_OPTIONS_SET = {"VIX", "VIXW", "SPX", "XSP"}


class ExerciseStyle(str, Enum):
    # make this an enum for American or European
    AMERICAN = "AMERICAN"
    EUROPEAN = "EUROPEAN"

    @staticmethod
    def from_ticker(ticker):
        if ticker in EUROPEAN_OPTIONS_SET:
            return ExerciseStyle.EUROPEAN
        return ExerciseStyle.AMERICAN

    @staticmethod
    def from_expiry_type(expiry_type: str):
        if not expiry_type:
            raise Exception(f"Could not parse expiry type: {expiry_type}")
        if expiry_type.lower() == "american":
            return ExerciseStyle.AMERICAN
        if expiry_type.lower() == "european":
            return ExerciseStyle.EUROPEAN
        else:
            raise Exception(f"Could not parse expiry type: {expiry_type}")
