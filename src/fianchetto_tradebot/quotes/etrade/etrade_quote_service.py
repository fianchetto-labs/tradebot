import json
import logging
from datetime import datetime

from fianchetto_tradebot.common.api.finance.greeks.greeks import Greeks
from fianchetto_tradebot.common.exchange.etrade.etrade_connector import ETradeConnector
from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.finance.chain import Chain
from fianchetto_tradebot.common.finance.equity import Equity
from fianchetto_tradebot.common.finance.option import Option
from fianchetto_tradebot.common.finance.option_type import OptionType
from fianchetto_tradebot.common.finance.price import Price
from fianchetto_tradebot.common.finance.priced_option import PricedOption
from fianchetto_tradebot.common.finance.tradable import Tradable
from fianchetto_tradebot.quotes.api.get_options_chain_request import GetOptionsChainRequest
from fianchetto_tradebot.quotes.api.get_options_chain_response import GetOptionsChainResponse
from fianchetto_tradebot.quotes.api.get_option_expire_dates_request import GetOptionExpireDatesRequest
from fianchetto_tradebot.quotes.api.get_option_expire_dates_response import GetOptionExpireDatesResponse
from fianchetto_tradebot.quotes.api.get_tradable_request import GetTradableRequest
from fianchetto_tradebot.quotes.api.get_tradable_response import GetTradableResponse
from fianchetto_tradebot.quotes.quote_service import QuoteService

logger = logging.getLogger(__name__)

class ETradeQuoteService(QuoteService):

    def get_tradable_quote(self, tradable_request: GetTradableRequest) -> GetTradableResponse:

        connector: ETradeConnector = self.connector
        session, base_url = connector.load_connection()

        tradable = tradable_request.get_tradable()
        if isinstance(tradable, Option):
            # format is: underlying:year:month:day:optionType:strikePrice.
            as_option: Option = tradable
            ticker = as_option.equity.ticker
            expiry = as_option.expiry
            strike = as_option.strike
            option_type = as_option.type
            symbols = f"{ticker}:{expiry.year}:{expiry.month}:{expiry.day}:{option_type}:{strike}"
        elif isinstance(tradable, Equity):
            as_option: Equity = tradable
            symbols = as_option.ticker
        else:
            raise Exception(f"Tradable type {type(tradable)} not recognized")

        path = f"/v1/market/quote/{symbols}.json"
        url = base_url + path
        response = session.get(url)

        tradable_response: GetTradableResponse = ETradeQuoteService._parse_market_response(tradable, response)

        return tradable_response

    def get_equity_quote(self, symbol: str):
        pass

    def get_options_chain(self, get_options_chain_request: GetOptionsChainRequest) -> GetOptionsChainResponse:
        connector: ETradeConnector = self.connector
        session, base_url = connector.load_connection()
        equity: Equity = get_options_chain_request.equity

        params: dict[str, str] = dict[str, str]()
        params["symbol"] = equity.ticker

        if get_options_chain_request.expiry:
            as_datetime: datetime.date = get_options_chain_request.expiry
            year = as_datetime.year
            month = as_datetime.month
            day = as_datetime.day

            params["expiryYear"] = year
            params["expiryMonth"] = month
            params["expiryDay"] = day


        path = f"/v1/market/optionchains.json"

        url = base_url + path
        response = session.get(url, params=params)
        options_chain = ETradeQuoteService._parse_options_chain(response, equity)

        return GetOptionsChainResponse(options_chain)

    def get_option_expire_dates(self, get_options_expire_dates_request: GetOptionExpireDatesRequest)-> GetOptionExpireDatesResponse:
        connector: ETradeConnector = self.connector
        session, base_url = connector.load_connection()

        path = f"/v1/market/optionexpiredate.json"
        params: dict[str, str] = dict[str, str]()
        params["symbol"] = get_options_expire_dates_request.symbol
        url = base_url + path
        response = session.get(url, params=params)

        exp_list: list[datetime.date] = ETradeQuoteService._parse_option_expire_dates(response)

        return GetOptionExpireDatesResponse(exp_list)

    def get_option_details(self, option: Option):
        pass


    @staticmethod
    def _parse_options_chain(input, equity:Equity):
        data: dict = json.loads(input.text)

        option_chain = Chain(equity)
        option_chain_response = data['OptionChainResponse']

        selected = option_chain_response["SelectedED"]
        expiry_day = selected["day"]
        expiry_month = selected["month"]
        expiry_year = selected["year"]

        expiry_date = datetime(expiry_year, expiry_month, expiry_day).date()
        option_pairs = option_chain_response["OptionPair"]
        for option_pair in option_pairs:
            # Note that exercise style is not available in the response, per the documentation. We'll need a good way to look it up.
            if "Call" in option_pair:
                call_details=option_pair["Call"]
                call = Option(equity, OptionType.CALL, Amount.from_string(str(call_details["strikePrice"])), expiry_date)
                price = Price(call_details["bid"], call_details["ask"], call_details["lastPrice"])
                po: PricedOption = PricedOption(call, price)
                option_chain.add(po)

            if "Put" in option_pair:
                put_details=option_pair["Put"]
                put = Option(equity, OptionType.PUT, Amount.from_string(str(put_details["strikePrice"])), expiry_date)
                price = Price(put_details["bid"], put_details["ask"], put_details["lastPrice"])
                po: PricedOption = PricedOption(put, price)
                option_chain.add(po)

        return option_chain


    @staticmethod
    def _parse_market_response(tradable: Tradable, input)->GetTradableResponse:
        data: dict = input.json()
        if data is not None and "QuoteResponse" in data and "QuoteData" in data["QuoteResponse"]:
            for quote in data["QuoteResponse"]["QuoteData"]:
                if quote is not None and "dateTime" in quote:
                    response_time = quote["dateTime"]
                else:
                    response_time = None
                if quote is not None and "All" in quote and "lastTrade" in quote["All"]:
                    if quote is not None and "All" in quote and "bid" in quote["All"] and "bidSize" in quote["All"]:
                        bid = quote["All"]["bid"]
                    else:
                        bid = None
                    if quote is not None and "All" in quote and "ask" in quote["All"] and "askSize" in quote["All"]:
                        ask = quote["All"]["ask"]
                    else:
                        ask = None
                    if quote is not None and "All" in quote and "totalVolume" in quote["All"]:
                        volume = quote["All"]["totalVolume"]
                    else:
                        volume = None
                if quote is not None and "option" in quote:
                    option_quote_details = quote["option"]
                    if "optionGreeks" in option_quote_details:
                        option_greeks = option_quote_details["optionGreeks"]
                        rho = option_greeks["rho"]
                        vega = option_greeks["vega"]
                        theta = option_greeks["theta"]
                        delta = option_greeks["delta"]
                        gamma = option_greeks["gamma"]
                        iv = option_greeks["iv"]
                        # This one is curious .. shouldn't this be an amount or price?
                        current_value: bool = option_greeks["currentValue"]
                        greeks = Greeks(delta, gamma, theta, vega, rho, iv, current_value)
                    else:
                        print(f"Warn - greeks not present in response for {tradable}")
                        greeks = None
                else:
                    greeks = None

                return GetTradableResponse(tradable, response_time, Price(bid, ask), volume, greeks)
            else:
                # Handle errors
                if data is not None and 'QuoteResponse' in data and 'Messages' in data["QuoteResponse"] \
                        and 'Message' in data["QuoteResponse"]["Messages"] \
                        and data["QuoteResponse"]["Messages"]["Message"] is not None:
                    for error_message in data["QuoteResponse"]["Messages"]["Message"]:
                        logger.error("Error: " + error_message["description"])
                else:
                    logger.error("Error: Quote API service error")
        else:
            logger.debug("Response Body: %s", input)
            logger.error("Error: Quote API service error")

    @staticmethod
    def _parse_option_expire_dates(response)->list[datetime.date] :
        data: dict = json.loads(response.text)

        exp_date_list = []
        options_expire_date_response = data['OptionExpireDateResponse']
        expiration_dates = options_expire_date_response['ExpirationDate']
        for expiration_date in expiration_dates:
            year = expiration_date["year"]
            month = expiration_date["month"]
            day = expiration_date["day"]
            exp_date_list.append(datetime(year, month, day).date())

        return exp_date_list