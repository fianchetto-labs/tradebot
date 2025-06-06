# 📈 TradeBot: Getting Started with an Exchange

Welcome to the TradeBot ecosystem! This guide will help you connect your first exchange and execute your first trade.

TradeBot currently supports:

- 🏦 **E*TRADE** – [API Docs](https://apisb.etrade.com/docs/api/overview.html)
- 🏦 **Charles Schwab** – [API Docs](https://developer.schwab.com/products/trader-api--individual)
- 🏦 **Interactive Brokers (IBKR)** – [API Docs](https://interactivebrokers.github.io/)

---

## 🔐 1. Authentication Overview

Each exchange requires an API key and secret to authenticate. These are stored in a `config.ini` file that you'll need to create (per exchange).

### How to Set Up

1. Navigate to the appropriate brokerage directory:
   - `src/fianchetto_tradebot/server/common/brokerage/etrade/`
   - `src/fianchetto_tradebot/server/common/brokerage/ikbr/`
   - `src/fianchetto_tradebot/server/common/brokerage/schwab/`

2. Copy the example config file:

```bash
cp config.example.ini config.ini
```

3. Open the new `config.ini` and fill in your API keys.  
   The `BASE_URL` values are already set and do **not** need to be changed.

---

## 🧾 Config File Format

Each exchange’s `config.ini` should follow this format:

```ini
[DEFAULT]
SANDBOX_BASE_URL=https://apisb.etrade.com
PROD_BASE_URL=https://api.etrade.com

[SANDBOX]
SANDBOX_API_KEY=<SANDBOX_API_KEY>
SANDBOX_API_SECRET=<SANDBOX_API_SECRET_KEY>

[PROD]
PROD_API_KEY=<PROD_API_KEY>
PROD_API_SECRET=<PROD_API_SECRET>
```

> 🔒 These `config.ini` files are already included in `.gitignore` — **do not commit them**.

---

## 🧪 2. Sandbox vs. Live

| Exchange     | Sandbox Support | Notes                                             |
|--------------|-----------------|---------------------------------------------------|
| E*TRADE      | ✅               | Fully-featured sandbox for testing                |
| Schwab       | ❌               | Use small trades or test data only               |
| IBKR         | ✅               | Paper Trading supported via TWS or Gateway       |



```python
from fianchetto_tradebot.server.common.brokerage.etrade.etrade_connector import ETradeConnector

connector: ETradeConnector = ETradeConnector()
```

> Enable sandbox mode in the client initialization:
At E*Trade login, at runtime, select `1` for the `Sandbox` option, `2` for `Live`. 
```
1) Sandbox Consumer Key
2) Live Consumer Key
3) Exit
Please select Consumer Key Type: 1
```

---

## 🚀 3. First Call: Verify Connection

Try pulling account info to ensure your credentials and config are working:

```python
from fianchetto_tradebot.client import TradeBotClient
from fianchetto_tradebot.models import GetAccountRequest

req = GetAccountRequest(brokerage="etrade", account_id="your_account_id")
response = TradeBotClient().get_account(req)
print(response)
```

You should see your account summary or positions if everything is correctly configured.

---

## 🛡️ 4. Security Tips

- Never commit `config.ini` files.
- Use encrypted secrets for production environments.
- Rotate keys and secrets regularly.
- Restrict key permissions during testing (read-only where possible).

---

## 🆘 Need Help?

- Open an issue on [GitHub](https://github.com/Fianchetto-Labs/TradeBot/issues)
- Or contact the maintainer:  
  📧 **aleks@fianchettolabs.com**
