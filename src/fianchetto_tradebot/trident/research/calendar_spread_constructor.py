import datetime

from pandas import DataFrame

from fianchetto_tradebot.common.exchange.etrade.etrade_connector import ETradeConnector
from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.finance.chain import Chain
from fianchetto_tradebot.common.finance.equity import Equity
from fianchetto_tradebot.common.finance.price import Price
from fianchetto_tradebot.quotes.api.get_option_expire_dates_request import GetOptionExpireDatesRequest
from fianchetto_tradebot.quotes.api.get_options_chain_request import GetOptionsChainRequest
from fianchetto_tradebot.quotes.api.get_options_chain_response import GetOptionsChainResponse
from fianchetto_tradebot.quotes.api.get_tradable_request import GetTradableRequest
from fianchetto_tradebot.quotes.etrade.etrade_quote_service import ETradeQuoteService
from fianchetto_tradebot.quotes.quote_service import QuoteService

from sortedcontainers import SortedDict

DEFAULT_NUM_STRIKES = 15
DEFAULT_DELTA_FROM_CURRENT_PRICE = 5

class CalendarSpreadCell:
    def __init__(self, starting_expiry: datetime.datetime.date, ending_expiry: datetime.datetime.date, atm_spread_value: (Amount, Amount), otm_spread_values: (Amount, Amount)):
        self.starting_expiry: datetime.datetime.date = starting_expiry
        self.ending_expiry: datetime.datetime.date = ending_expiry
        self.atm_spread_values: (Amount, Amount) = atm_spread_value
        self.otm_spread_values: (Amount, Amount) = otm_spread_values

        self.atm_spread_value: Amount = self.atm_spread_values[1] - self.atm_spread_values[0]
        self.otm_spread_value: Amount = self.otm_spread_values[1] - self.otm_spread_values[0]

        # This is the ratio between the reference calendar spread at that date, vs the OTM one
        self.ratio: float = self.get_price_ratio()
        # This is the price difference between the reference calendar spread at that date, vs the OTM one
        self.price_difference = self.get_price_difference()

    def get_price_ratio(self) -> float:
        return float(self.atm_spread_value / self.otm_spread_value)

    def get_price_difference(self) -> Amount:
        return self.atm_spread_value - self.otm_spread_value

class CalendarSpreadConstructor:
    def __init__(self, qs: QuoteService, equity: Equity, num_strikes: int = DEFAULT_NUM_STRIKES):
        # The number of strikes into the future
        self.qs:QuoteService = qs
        self.num_strikes: int = num_strikes

        # The security in question
        self.equity: Equity = equity

        self.options_chain: Chain = self.build_options_chain()

    def build_options_chain(self) -> Chain:
        get_option_expire_dates_request = GetOptionExpireDatesRequest(self.equity.ticker)
        option_expire_dates_response = self.qs.get_option_expire_dates(get_option_expire_dates_request)

        options_chain = Chain(self.equity)
        for expiry in option_expire_dates_response.expire_dates[:self.num_strikes]:
            get_options_chain_request: GetOptionsChainRequest = GetOptionsChainRequest(self.equity, expiry)
            get_options_chain_response: GetOptionsChainResponse = self.qs.get_options_chain(get_options_chain_request)
            options_list = get_options_chain_response.options_chain

            print(f"Adding options from {expiry}")
            options_chain.add_chain(options_list)

        return options_chain

    def get_current_price(self)->float:
        return self.qs.get_tradable_quote(GetTradableRequest(tradable=self.equity)).current_price.mark

    def build_matrix(self, delta_from_current_price: int=DEFAULT_DELTA_FROM_CURRENT_PRICE) -> DataFrame:
        current_price = self.get_current_price()

        # to nearest $.5
        #current_price_to_nearest_dollar: float = round(current_price*2)/2
        atm_price_float: float = round(current_price)
        atm_price = Amount.from_float(atm_price_float)
        print(f"Current price to nearest dollar is: {atm_price}")

        calls = self.options_chain.strike_expiry_chain_call
        puts = self.options_chain.strike_expiry_chain_put

        otm_call_price = Amount.from_float(atm_price_float + delta_from_current_price)
        otm_put_price = Amount.from_float(atm_price_float - delta_from_current_price)

        otm_call_chain: dict[datetime, Price] = SortedDict(calls[otm_call_price])
        otm_put_chain: dict[datetime, Price] = SortedDict(puts[otm_put_price])

        atm_call_chain: dict[datetime, Price] = SortedDict(calls[atm_price])
        atm_put_chain: dict[datetime, Price] = SortedDict(puts[atm_price])

        otm_call_output: dict[datetime, datetime, CalendarSpreadCell] = dict[datetime, datetime, CalendarSpreadCell]()
        otm_put_output: dict[datetime, datetime, CalendarSpreadCell] = dict[datetime, datetime, CalendarSpreadCell]()

        atm_call_output: dict[datetime, datetime, CalendarSpreadCell] = dict[datetime, datetime, CalendarSpreadCell]()
        atm_put_output: dict[datetime, datetime, CalendarSpreadCell] = dict[datetime, datetime, CalendarSpreadCell]()

        # Calls
        for calendar_start_index, (calendar_start_date, otm_start_price)  in enumerate(otm_call_chain.items()):
            for calendar_end_index, (calendar_end_date,  otm_end_price) in enumerate(otm_call_chain.items()):
                if calendar_start_date >= calendar_end_date:
                    continue

                otm_prices = (Amount.from_float(otm_start_price.mark), Amount.from_float(otm_end_price.mark))
                atm_prices = (Amount.from_float(atm_call_chain[calendar_start_date].mark), Amount.from_float(atm_call_chain[calendar_end_date].mark))
                cell = CalendarSpreadCell(calendar_start_date, calendar_end_date, atm_prices, otm_prices)

                if calendar_start_date not in otm_call_output:
                    otm_call_output[calendar_start_date] = dict[datetime, CalendarSpreadCell]()
                otm_call_output[calendar_start_date][calendar_end_index] = cell

        # Puts
        for calendar_start_index, (calendar_start_date, otm_start_price) in enumerate(otm_put_chain.items()):
            for calendar_end_index, (calendar_end_date, otm_end_price) in enumerate(otm_put_chain.items()):
                if calendar_start_date >= calendar_end_date:
                    continue

                otm_prices = (Amount.from_float(otm_start_price.mark), Amount.from_float(otm_end_price.mark))
                atm_prices = (Amount.from_float(atm_put_chain[calendar_start_date].mark),
                              Amount.from_float(atm_put_chain[calendar_end_date].mark))
                cell = CalendarSpreadCell(calendar_start_date, calendar_end_date, atm_prices, otm_prices)
                if calendar_start_date not in otm_put_output:
                    otm_put_output[calendar_start_date] = dict[datetime, CalendarSpreadCell]()
                otm_put_output[calendar_start_date][calendar_end_index] = cell


if __name__ == "__main__":
    connector: ETradeConnector = ETradeConnector()
    q: QuoteService = ETradeQuoteService(connector)

    ticker = "SPY"
    equity_name = "SPDR S&P 500 ETF TRUST"

    equity: Equity = Equity(ticker, equity_name)
    constructor = CalendarSpreadConstructor(q, equity, 4)
    constructor.build_matrix()