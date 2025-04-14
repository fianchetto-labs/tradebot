from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.finance.currency import Currency

ZERO_AMOUNT = Amount(whole=0, part=0, currency=Currency.US_DOLLARS)

class ComputedBalance:
    def __init__(self, cash_available_for_investment: Amount = ZERO_AMOUNT,
                 cash_available_for_withdrawal: Amount = ZERO_AMOUNT,
                 total_available_for_withdrawal: Amount = ZERO_AMOUNT, net_cash: Amount = ZERO_AMOUNT,
                 cash_balance: Amount = ZERO_AMOUNT, margin_buying_power: Amount = ZERO_AMOUNT,
                 cash_buying_power: Amount = ZERO_AMOUNT, margin_balance:Amount = ZERO_AMOUNT,
                 account_balance: Amount = ZERO_AMOUNT):
        self.cash_available_for_investment: Amount = cash_available_for_investment
        self.cash_available_for_withdrawal: Amount = cash_available_for_withdrawal
        self.total_available_for_withdrawal: Amount = total_available_for_withdrawal
        self.net_cash: Amount = net_cash
        self.cash_balance: Amount = cash_balance
        self.margin_buying_power: Amount = margin_buying_power
        self.cash_buying_power: Amount = cash_buying_power
        self.margin_balance = margin_balance
        self.account_balance: Amount = account_balance