import asyncio
import json
import logging
from datetime import date

from dateutil.parser import parse

from fianchetto_tradebot.common.api.finance.greeks.greeks import Greeks
from fianchetto_tradebot.common.brokerage.etrade.etrade_connector import ETradeConnector
from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.finance.chain import ChainBuilder, Chain
from fianchetto_tradebot.common.finance.equity import Equity
from fianchetto_tradebot.common.finance.option import Option
from fianchetto_tradebot.common.finance.option_type import OptionType
from fianchetto_tradebot.common.finance.price import Price
from fianchetto_tradebot.common.finance.priced_option import PricedOption
from fianchetto_tradebot.common.finance.tradable import Tradable
from fianchetto_tradebot.quotes.api.get_option_expire_dates_request import GetOptionExpireDatesRequest
from fianchetto_tradebot.quotes.api.get_option_expire_dates_response import GetOptionExpireDatesResponse
from fianchetto_tradebot.quotes.api.get_options_chain_request import GetOptionsChainRequest
from fianchetto_tradebot.quotes.api.get_options_chain_response import GetOptionsChainResponse
from fianchetto_tradebot.quotes.api.get_tradable_request import GetTradableRequest
from fianchetto_tradebot.quotes.api.get_tradable_response import GetTradableResponse
from fianchetto_tradebot.quotes.quotes_service import QuotesService

logger = logging.getLogger(__name__)

class ETradeQuotesService(QuotesService):
    def __init__(self, connector: ETradeConnector):
        super().__init__(connector)
        self.session, self.async_session, self.base_url = connector.load_connection()

    def get_tradable_quote(self, tradable_request: GetTradableRequest) -> GetTradableResponse:
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
        url = self.base_url + path
        response = self.session.get(url)

        tradable_response: GetTradableResponse = ETradeQuotesService._parse_market_response(tradable, response)

        return tradable_response

    def get_equity_quote(self, symbol: str):
        # TODO: Implement this
        pass

    def get_options_chain_sequential(self, get_options_chain_request: GetOptionsChainRequest) -> GetOptionsChainResponse:
        equity: Equity = Equity(ticker=get_options_chain_request.ticker)

        params: dict[str, str] = dict[str, str]()
        params["symbol"] = equity.ticker

        # Default behavior, if expiry is not provided, is to deliver the chain at the most upcoming expiry
        if get_options_chain_request.expiry:
            as_datetime: date = get_options_chain_request.expiry
            year = as_datetime.year
            month = as_datetime.month
            day = as_datetime.day

            params["expiryYear"] = year
            params["expiryMonth"] = month
            params["expiryDay"] = day

        params["expiryYear"] = '2025'
        path = f"/v1/market/optionchains.json"
        url = self.base_url + path
        response = self.session.get(url, params=params)
        options_chain = ETradeQuotesService._parse_options_chain(response, equity)

        return GetOptionsChainResponse(options_chain=options_chain)

    async def _assemble_individual_option_expiry_requests(self, ticker: str, expiries: list[date]) -> list:
        tasks = [self.get_options_chain_task(ticker, expiry) for expiry in expiries]
        return await asyncio.gather(*tasks)

    def get_options_chain(self, get_options_chain_request: GetOptionsChainRequest)->GetOptionsChainResponse:
        ticker = get_options_chain_request.ticker

        if get_options_chain_request.expiry:
            expiries = [get_options_chain_request.expiry]
        else:
            expiries: list[date] = self.get_option_expire_dates(GetOptionExpireDatesRequest(ticker=ticker)).expire_dates

        results = asyncio.run(self._assemble_individual_option_expiry_requests(ticker, expiries))

        cb: ChainBuilder = ChainBuilder(Equity(ticker=ticker))
        for result in results:
            cb.add_chain(result)

        return GetOptionsChainResponse(options_chain=cb.to_chain())

    async def get_options_chain_task(self, ticker:str, expiry: date) -> Chain:
        params: dict[str, str] = dict[str, str]()

        params["expiryYear"] = expiry.year
        params["expiryMonth"] = expiry.month
        params["expiryDay"] = expiry.day

        params["symbol"] = ticker

        path = f"/v1/market/optionchains.json"
        url = self.base_url + path

        # Open question about the params...do I need to manually add to URI?
        response: dict = await self.async_session.request(method="GET", url=url, params=params)
        return ETradeQuotesService._parse_options_chain_dict(response, Equity(ticker=ticker))

    def get_option_expire_dates(self, get_options_expire_dates_request: GetOptionExpireDatesRequest)-> GetOptionExpireDatesResponse:
        path = f"/v1/market/optionexpiredate.json"
        params: dict[str, str] = dict[str, str]()
        params["symbol"] = get_options_expire_dates_request.ticker
        url = self.base_url + path
        response = self.session.get(url, params=params)

        exp_list: list[date] = ETradeQuotesService._parse_option_expire_dates(response)

        return GetOptionExpireDatesResponse(expire_dates=exp_list)

    def get_option_details(self, option: Option):
        pass

    @staticmethod
    def _parse_options_chain(input, equity: Equity)->Chain:
        return ETradeQuotesService._parse_options_chain_dict(input.text, equity)

    @staticmethod
    def _parse_options_chain_dict(data:dict, equity:Equity)->Chain:
        option_chain_builder = ChainBuilder(equity)
        if 'OptionChainResponse' not in data:
            print(f"Option Chain Response not available - {data}")
            return option_chain_builder.to_chain()

        option_chain_response = data['OptionChainResponse']

        if 'OptionPair' not in option_chain_response:
            print(f"Could not parse options chain {option_chain_response}")
            return option_chain_builder.to_chain()

        selected = option_chain_response["SelectedED"]
        expiry_day = selected["day"]
        expiry_month = selected["month"]
        expiry_year = selected["year"]

        expiry_date: date = date(expiry_year, expiry_month, expiry_day)
        option_pairs = option_chain_response["OptionPair"]
        for option_pair in option_pairs:
            # Note that exercise style is not available in the response, per the documentation. We'll need a good way to look it up.
            if "Call" in option_pair:
                call_details=option_pair["Call"]
                call = Option(equity=equity, type=OptionType.CALL, strike=Amount.from_string(str(call_details["strikePrice"])), expiry=expiry_date)
                price = Price(bid=call_details["bid"], ask=call_details["ask"], last=call_details["lastPrice"])
                po: PricedOption = PricedOption(option=call, price=price)
                option_chain_builder.add(po)

            if "Put" in option_pair:
                put_details=option_pair["Put"]
                put = Option(equity=equity, type=OptionType.PUT, strike=Amount.from_string(str(put_details["strikePrice"])), expiry=expiry_date)
                price = Price(bid=put_details["bid"], ask=put_details["ask"], last=put_details["lastPrice"])
                po: PricedOption = PricedOption(option=put, price=price)
                option_chain_builder.add(po)

        return option_chain_builder.to_chain()

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
                        greeks = Greeks(delta=delta, gamma=gamma, theta=theta, vega=vega, rho=rho, iv=iv, current_value=current_value)
                    else:
                        print(f"Warn - greeks not present in response for {tradable}")
                        greeks = None
                else:
                    greeks = None
                return GetTradableResponse(tradable=tradable, response_time=parse(response_time), current_price=Price(bid=bid, ask=ask), volume=volume, greeks=greeks)
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
    def _parse_option_expire_dates(response)->list[date] :
        data: dict = json.loads(response.text)

        exp_date_list = []
        options_expire_date_response = data['OptionExpireDateResponse']
        expiration_dates = options_expire_date_response['ExpirationDate']
        for expiration_date in expiration_dates:
            year = expiration_date["year"]
            month = expiration_date["month"]
            day = expiration_date["day"]
            exp_date_list.append(date(year, month, day))

        return exp_date_list

    def _get_async_session_from_session(self):
        from aioauth_client import OAuth1Client

        client = OAuth1Client(
            client_id="consumer_key",
            client_secret="consumer_secret",
            resource_owner_key="access_token",
            resource_owner_secret="access_token_secret",
            base_url="https://api.etrade.com"
        )