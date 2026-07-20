ACCOUNT_ID = "acct-key-1"
ACCOUNT_DISPLAY_ID = "acct-1"
EQUITY_SYMBOL = "GE"
PREVIEW_ID = "preview-1"
ORDER_ID = "order-1"
RESPONSE_TIMESTAMP = "2026-01-02T13:30:00Z"


def account_list_response() -> dict:
    return {
        "AccountListResponse": {
            "Accounts": {
                "Account": [
                    {
                        "accountId": ACCOUNT_DISPLAY_ID,
                        "accountIdKey": ACCOUNT_ID,
                        "accountName": "Demo Margin",
                        "accountDesc": "Individual Brokerage",
                    }
                ]
            }
        }
    }


def balance_response(account_id: str = ACCOUNT_ID) -> dict:
    return {
        "BalanceResponse": {
            "accountId": account_id,
            "Computed": {
                "RealTimeValues": {"totalAccountValue": 125000.25},
                "OpenCalls": {
                    "fedCall": 0,
                    "maintenanceCall": -250.00,
                },
                "settledCashForInvestment": 10000.00,
                "unSettledCashForInvestment": 250.25,
                "cashAvailableForWithdrawal": 9000.00,
                "netCash": 10250.25,
                "cashBalance": 10250.25,
                "marginBuyingPower": 50000.00,
                "cashBuyingPower": 10000.00,
                "marginBalance": 0.00,
                "accountBalance": 125000.25,
            },
        }
    }


def portfolio_response(account_id: str = ACCOUNT_ID) -> dict:
    return {
        "PortfolioResponse": {
            "AccountPortfolio": [
                {
                    "accountId": account_id,
                    "Position": [
                        {
                            "quantity": 100,
                            "Product": {
                                "securityType": "EQ",
                                "symbol": EQUITY_SYMBOL,
                            },
                            "Complete": {"symbolDescription": "General Electric"},
                        },
                        {
                            "quantity": -1,
                            "Product": {
                                "securityType": "OPTN",
                                "symbol": EQUITY_SYMBOL,
                                "callPut": "PUT",
                                "strikePrice": 25.00,
                                "expiryYear": 2026,
                                "expiryMonth": 1,
                                "expiryDay": 16,
                            },
                            "Complete": {"symbolDescription": "GE Jan 2026 25 Put"},
                        },
                    ],
                }
            ]
        }
    }


def quote_response(symbol: str, include_greeks: bool = False) -> dict:
    quote_data = {
        "dateTime": RESPONSE_TIMESTAMP,
        "symbolDescription": symbol,
        "All": {
            "bid": 100.00,
            "bidSize": 10,
            "ask": 101.00,
            "askSize": 12,
            "lastTrade": 100.50,
            "totalVolume": 1000,
        },
    }
    if include_greeks:
        quote_data["option"] = {
            "optionGreeks": {
                "rho": -0.01,
                "vega": 0.12,
                "theta": -0.03,
                "delta": -0.40,
                "gamma": 0.05,
                "iv": 0.22,
                "currentValue": {"bid": 1.40, "ask": 1.60},
            }
        }

    return {"QuoteResponse": {"QuoteData": [quote_data]}}


def option_expire_date_response() -> dict:
    return {
        "OptionExpireDateResponse": {
            "ExpirationDate": [
                {"year": 2026, "month": 1, "day": 16},
                {"year": 2026, "month": 2, "day": 20},
            ]
        }
    }


def option_chain_response(year: int, month: int, day: int) -> dict:
    strike = 25.00 if month == 1 else 30.00
    return {
        "OptionChainResponse": {
            "SelectedED": {"year": year, "month": month, "day": day},
            "OptionPair": [
                {
                    "Call": {
                        "strikePrice": strike,
                        "bid": 1.10 if month == 1 else 2.90,
                        "ask": 1.20 if month == 1 else 3.10,
                        "lastPrice": 1.15 if month == 1 else 3.00,
                    },
                    "Put": {
                        "strikePrice": strike,
                        "bid": 1.40 if month == 1 else 3.20,
                        "ask": 1.60 if month == 1 else 3.30,
                        "lastPrice": 1.50 if month == 1 else 3.25,
                    },
                }
            ],
        }
    }


def preview_order_response() -> dict:
    order = etrade_order_json()
    order["estimatedTotalAmount"] = 100.00
    order["estimatedCommission"] = 0.00
    return {
        "PreviewOrderResponse": {
            "PreviewIds": [{"previewId": PREVIEW_ID}],
            "Order": [order],
        }
    }


def place_order_response(order_id: str = ORDER_ID) -> dict:
    order = etrade_order_json()
    order["messages"] = {
        "Message": [
            {
                "description": "Order placed",
                "code": 1027,
                "type": "INFO",
            }
        ]
    }
    return {
        "PlaceOrderResponse": {
            "orderType": "EQ",
            "OrderIds": [{"orderId": order_id}],
            "Order": [order],
        }
    }


def get_order_response(order_id: str = ORDER_ID, status: str = "OPEN") -> dict:
    return {
        "OrdersResponse": {
            "Order": [
                {
                    "orderId": order_id,
                    "OrderDetail": [etrade_order_json(status=status, include_market_values=True)],
                }
            ]
        }
    }


def cancel_order_response(order_id: str = ORDER_ID) -> dict:
    return {
        "CancelOrderResponse": {
            "orderId": order_id,
            "cancelTime": "2026-01-02T13:31:00Z",
            "Messages": {
                "Message": [
                    {
                        "description": "Order canceled",
                        "code": 5011,
                        "type": "INFO",
                    }
                ]
            },
        }
    }


def retryable_preview_error_response() -> dict:
    return {
        "Error": {
            "code": 167,
            "message": "We did not find enough available shares of this security in your account.",
        }
    }


def etrade_order_json(status: str | None = None, include_market_values: bool = False) -> dict:
    order = {
        "accountId": ACCOUNT_ID,
        "allOrNone": False,
        "orderTerm": "GOOD_FOR_DAY",
        "priceType": "LIMIT",
        "limitPrice": 100.00,
        "Instrument": [
            {
                "orderedQuantity": 1,
                "filledQuantity": 0,
                "orderAction": "BUY",
                "Product": {
                    "securityType": "EQ",
                    "symbol": EQUITY_SYMBOL,
                },
            }
        ],
    }

    if status:
        order["status"] = status
    if include_market_values:
        order.update(
            {
                "placedTime": 1767360600000,
                "marketSession": "REGULAR",
                "netPrice": -100.50,
                "netBid": -100.00,
                "netAsk": -101.00,
            }
        )

    return order
