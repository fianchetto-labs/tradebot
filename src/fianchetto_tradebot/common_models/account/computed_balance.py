from pydantic import BaseModel

from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.finance.currency import Currency

ZERO_AMOUNT = Amount(whole=0, part=0, currency=Currency.US_DOLLARS)

class ComputedBalance(BaseModel):
    cash_available_for_investment: Amount = ZERO_AMOUNT
    cash_available_for_withdrawal: Amount = ZERO_AMOUNT
    total_available_for_withdrawal: Amount = ZERO_AMOUNT
    net_cash: Amount = ZERO_AMOUNT
    cash_balance: Amount = ZERO_AMOUNT
    margin_buying_power: Amount = ZERO_AMOUNT
    cash_buying_power: Amount = ZERO_AMOUNT
    margin_balance: Amount = ZERO_AMOUNT
    account_balance: Amount = ZERO_AMOUNT