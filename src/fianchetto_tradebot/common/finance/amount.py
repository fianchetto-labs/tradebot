import math

from pydantic import BaseModel

from fianchetto_tradebot.common.finance.currency import Currency


class Amount(BaseModel):
    whole: int
    part: int
    currency: Currency = Currency.US_DOLLARS
    negative: bool = False


    @staticmethod
    def __validate__(whole, part):
        # TODO: Use pydantic validation -- this is the basic logic though
        if whole < 0 or part < 0:
            raise Exception("Please only include magnitude, for part and whole. Sign set using negative field")
        if part > 99:
            raise Exception("Invalid value for part")

    @staticmethod
    def from_string(input_str: str, currency=Currency.US_DOLLARS):
        if not input_str:
            raise Exception("could not parse input")

        if "." in input_str:
            (whole, part) = input_str.split('.')
            part = part[:2]
            # To compensate for the fact that turning a float into a string will truncate the ending 0, turning
            # an '80' into an '8'.
            if len(part) == 1:
                part = int(part)*10
        else:
            input_str = input_str.strip("$")
            whole = input_str
            part = 0

        negative = input_str.startswith('-')
        whole = ''.join(c for c in whole if (c.isdigit()))

        return Amount(whole=int(whole), part=int(part), currency=currency, negative=negative)

    @staticmethod
    def from_float(input_float: float, currency=Currency.US_DOLLARS):
        if input_float is None:
            raise Exception("could not parse input")

        if input_float == 0.0 or input_float == 0:
            return Amount(whole=0, part=0, currency=currency)

        return Amount.from_string(str(input_float), currency)

    def __add__(self, other):
        if other.currency != self.currency:
            raise Exception("implicit currency conversion not supported")

        total = self.in_smallest_denomination() + other.in_smallest_denomination()

        new_whole: int = math.floor(abs(total) / 100)
        new_part: int = abs(total) % 100

        negative: bool = True if total < 0 else False

        return Amount(whole=abs(new_whole), part=new_part, currency=self.currency, negative=negative)

    def __sub__(self, other):
        if other.currency != self.currency:
            raise Exception("implicit currency conversion not supported")

        total = self.in_smallest_denomination() - other.in_smallest_denomination()

        new_whole: int = math.floor(abs(total) / 100)
        new_part: int = abs(total) % 100

        return Amount(whole=new_whole, part=new_part, currency=self.currency, negative=total < 0)

    # This is a scalar operation, returning an Amount, as it makes no sense to multiply two amounts together (units would be Currency^2)
    def __mul__(self, other: float):
        total: float = float(abs(self.in_smallest_denomination())) * abs(other)
        negative = self.negative ^ (other < 0)


        new_whole: int = math.floor(total / 100)
        new_part: int = round(total % 100)

        return Amount(whole=new_whole, part=new_part, currency=self.currency, negative=negative)

    # This can be a scalar operation (units are Currency). It can also be a simple float b/c we'd get a ratio if we divided two values.
    def __truediv__(self, other)->float:
        if other.currency != self.currency:
            raise Exception("implicit currency conversion not supported")

        total: float = float(float(self.in_smallest_denomination()) / float(other.in_smallest_denomination()))
        return round(total, 2)

    def in_smallest_denomination(self) -> int:
        nominal = self.whole * 100 + self.part
        if self.negative:
            return -1 * nominal
        return nominal

    def to_float(self):
        absolute_value = self.whole + self.part / 100.0
        if self.negative:
            return -1 * absolute_value
        else:
            return absolute_value

    def __str__(self):
        return f"{self.to_float():.2f}"

    def __repr__(self):
        return self.__str__()

    def __abs__(self):
        return Amount.from_float(abs(self.to_float()))

    def __le__(self, other):
        nominal: int = self.whole * 100 + self.part
        nominal_other: int = other.whole * 100 + other.part
        if self.negative:
            nominal = -1 * nominal
        if other.negative:
            nominal_other = -1 * nominal_other

        return nominal < nominal_other

    def __gt__(self, other):
        return not self.__le__(other)

    def __eq__(self, other):
        if other.currency and self.currency and other.currency != self.currency:
            return False

        if other.whole != self.whole:
            return False

        if other.part != self.part:
            return False

        if other.negative != self.negative:
            return False

        return True

    def __hash__(self):
        # TODO: Figure out a more standard way of hashing
        return hash(str(self.whole) + str(self.part) + str(self.currency))


ZERO = Amount(whole=0,part=0)