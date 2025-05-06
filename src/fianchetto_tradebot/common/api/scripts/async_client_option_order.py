import asyncio
import configparser
import os
from datetime import datetime, date
from random import uniform

from fianchetto_tradebot.common.brokerage.etrade.etrade_connector import ETradeConnector

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'integration_test_properties.ini')
ACCOUNT_ID_KEY = 'ACCOUNT_ID_KEY'

JAN_1_2024: date = date(2024, 1, 1)
JAN_2_2024: date = date(2024, 1, 2)

TODAY = datetime.now().date()
MAX_COUNT = 1000

config = configparser.ConfigParser()


def account_key():
    return config['ETRADE'][ACCOUNT_ID_KEY]

def get_credentials():
    config.read(CONFIG_FILE)
    connector: ETradeConnector = ETradeConnector()
    session, async_session, base_url = connector.load_connection()

    return base_url, session, async_session

async def get_endpoints():
    base_url, session, async_session = get_credentials()

    option_expire_path = f"/v1/market/optionexpiredate.json"
    option_expire_url = base_url + option_expire_path

    equity_quote_path = f"/v1/market/quote/GE.json"
    equity_quote_url = base_url + equity_quote_path

    urls = [option_expire_url, equity_quote_url]

    #tasks = [fetch(async_session, url) for url in urls]
    tasks = [print_time(id, url) for id, url in zip([1,2], urls)]
    return await asyncio.gather(*tasks)


async def fetch(session, url):
    async with session.request(method="GET", url=url) as response:
        return await response.json()

async def assemble_simple_tasks(session, base_url):
    p1 = f"{base_url}/v1/market/optionchains.json"
    p2 = f"{base_url}/v1/market/optionchains.json"

    urls = [p1, p2]

    tasks = [print_time(id, url, s) for (id, url, s) in zip([1,2], urls, [session, session])]
    return await asyncio.gather(*tasks)

async def print_time(id, url, session):
    print(f"{id}: {datetime.now()} - {url}")
    random_time = uniform(2,5)
    print(f"{id}: {datetime.now()} Pausing {random_time} seconds")

    #await asyncio.sleep(random_time)
    #await requests.get(url) #The response cannot be used in an await expression. makes sense. Seems like there's some
    # kind of API or interface that needs to be implemented by the method

    result = await session.request(method="GET", url=url, params={"symbol": "GE"})
    print(result)
    print(f"{id}: {datetime.now()} Finally done! ")

if __name__ == "__main__":
    config.read(CONFIG_FILE)
    connector: ETradeConnector = ETradeConnector()
    session, async_session, base_url = connector.load_connection()

    uri =  f"{base_url}/v1/market/optionchains.json"
    response = session.get(url=uri, params={"symbol": "GE"})
    print(response.json())

    results = asyncio.run(assemble_simple_tasks(async_session, base_url))