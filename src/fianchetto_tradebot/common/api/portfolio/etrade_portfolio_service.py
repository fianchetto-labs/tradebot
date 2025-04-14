import datetime
import json

from fianchetto_tradebot.common.api.portfolio.get_portfolio_request import GetPortfolioRequest
from fianchetto_tradebot.common.api.portfolio.get_portfolio_response import GetPortfolioResponse
from fianchetto_tradebot.common.api.portfolio.portfolio_service import PortfolioService
from fianchetto_tradebot.common.exchange.connector import Connector
from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.finance.equity import Equity
from fianchetto_tradebot.common.finance.option import Option
from fianchetto_tradebot.common.finance.exercise_style import ExerciseStyle
from fianchetto_tradebot.common.finance.option_type import OptionType
from fianchetto_tradebot.common.finance.tradable import Tradable
from fianchetto_tradebot.common.portfolio.portfolio import Portfolio

DEFAULT_SORT_BY = "DAYS_EXPIRATION"
DEFAULT_SORT_ORDER = "ASC"

DEFAULT_VIEW = "COMPLETE"

DEFAULT_NUM_POSITIONS = 1000

DEFAULT_PORTFOLIO_OPTIONS = {
    "sortBy": DEFAULT_SORT_BY,
    "sortOrder": DEFAULT_SORT_ORDER,
    "view": DEFAULT_VIEW,
    "count": str(DEFAULT_NUM_POSITIONS)
}


class ETradePortfolioService(PortfolioService):
    def __init__(self, connector: Connector):
        super().__init__(connector)
        self.session, self.base_url = self.connector.load_connection()

    def get_portfolio_info(self, get_portfolio_request: GetPortfolioRequest, exchange_specific_options: dict[str, str] = DEFAULT_PORTFOLIO_OPTIONS) -> GetPortfolioResponse:
        account_id_key = get_portfolio_request.account_id

        path = f"/v1/accounts/{account_id_key}/portfolio.json"

        params: dict[str, str] = dict()
        params["count"] = str(DEFAULT_NUM_POSITIONS)
        if exchange_specific_options:
            for k,v in exchange_specific_options.items():
                params[k]=v

        url = self.base_url + path
        # approach 1
        response = self.session.get(url, params=params)
        print(response.request.headers)
        print(response.url)

        portfolio_list_response = ETradePortfolioService._parse_portfolio_response(response)
        return portfolio_list_response

    @staticmethod
    def _parse_portfolio_response(input) -> GetPortfolioResponse:
        if input.status_code != 200:
            text = json.loads(input.text)
            error = text['Error']
            message = error['message']
            status_code = input.status_code
            raise Exception(f"Status {status_code}, {message}")
        data: dict = json.loads(input.text)
        portfolio_response = data["PortfolioResponse"]
        account_portfolios = portfolio_response["AccountPortfolio"]

        return_portfolio = Portfolio()
        for account_portfolio in account_portfolios:
            positions = account_portfolio["Position"]

            for position in positions:
                tradable = ETradePortfolioService._get_tradable_from_position(position)
                quantity = position["quantity"]
                return_portfolio.add_position(tradable, quantity)

        return GetPortfolioResponse(return_portfolio)

    @staticmethod
    def _get_tradable_from_position(position) -> Tradable:
        product = position["Product"]
        symbol = product["symbol"]
        symbol_desc = position["Complete"]["symbolDescription"]

        e = Equity(symbol, symbol_desc)

        if product["securityType"] == "EQ":
            return e
        elif product["securityType"] == "OPTN":
            option_type: OptionType = OptionType.from_str(product["callPut"])
            strike_price: Amount = Amount.from_string(str(product["strikePrice"]))
            exercise_style: ExerciseStyle = ExerciseStyle.AMERICAN if "expiryType" not in product else ExerciseStyle.from_expiry_type(product["expiryType"])
            expiry_year: int = product["expiryYear"]
            expiry_day: int = product["expiryDay"]
            expiry_month: int = product["expiryMonth"]
            return Option(e, option_type, strike_price, datetime.datetime(expiry_year, expiry_month, expiry_day).date(), exercise_style)
        else:
            raise Exception(f"Style {product['securityType']} not supported yet")


