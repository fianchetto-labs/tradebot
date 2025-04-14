import configparser
import datetime
import logging
import os
from pathlib import Path

from rauth import OAuth1Service, OAuth1Session
import pickle
import webbrowser

from fianchetto_tradebot.common.exchange.connector import Connector

config = configparser.ConfigParser()

DEFAULT_ETRADE_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.ini')
DEFAULT_ETRADE_SESSION_FILE = os.path.join(os.path.dirname(__file__), 'etrade_session.out')
DEFAULT_ETRADE_BASE_URL_FILE = os.path.join(os.path.dirname(__file__), 'etrade_base_url.out')

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "E*TRADE"


class ETradeConnector(Connector):

    def __init__(self, config_file=DEFAULT_ETRADE_CONFIG_FILE, session_file=DEFAULT_ETRADE_SESSION_FILE, base_url_file=DEFAULT_ETRADE_BASE_URL_FILE):
        self.exchange = EXCHANGE_NAME
        self.config_file = config_file
        self.session_file = session_file
        self.base_url_file = base_url_file

    def load_base_url(self) -> str:
        persisted_file = self.base_url_file
        if ETradeConnector.is_file_still_valid(persisted_file):
            return ETradeConnector.deserialize_session(persisted_file)

        return self.establish_connection()[1]

    def load_connection(self) -> (OAuth1Session, str):
        persisted_session_file = self.session_file
        persisted_base_url_file = self.base_url_file
        if ETradeConnector.is_file_still_valid(persisted_session_file) and ETradeConnector.is_file_still_valid(persisted_base_url_file):
            return ETradeConnector.deserialize_session(persisted_session_file), ETradeConnector.deserialize_session(persisted_base_url_file)

        return self.establish_connection()

    def establish_connection(self) -> (OAuth1Session, str):
        config.read(self.config_file)
        sandbox_etrade = OAuth1Service(
            name="etrade",
            consumer_key=config["SANDBOX"]["SANDBOX_API_KEY"],
            consumer_secret=config["SANDBOX"]["SANDBOX_API_SECRET"],
            request_token_url="https://api.etrade.com/oauth/request_token",
            access_token_url="https://api.etrade.com/oauth/access_token",
            authorize_url="https://us.etrade.com/e/t/etws/authorize?key={}&token={}",
            base_url="https://api.etrade.com")

        prod_etrade = OAuth1Service(
            name="etrade",
            consumer_key=config["PROD"]["PROD_API_KEY"],
            consumer_secret=config["PROD"]["PROD_API_SECRET"],
            request_token_url="https://api.etrade.com/oauth/request_token",
            access_token_url="https://api.etrade.com/oauth/access_token",
            authorize_url="https://us.etrade.com/e/t/etws/authorize?key={}&token={}",
            base_url="https://api.etrade.com")

        menu_items = {"1": "Sandbox Consumer Key",
                      "2": "Live Consumer Key",
                      "3": "Exit"}

        while True:
            print("")
            options = menu_items.keys()
            for entry in options:
                print(entry + ")\t" + menu_items[entry])
            selection = input("Please select Consumer Key Type: ")
            if selection == "1":
                base_url = config["DEFAULT"]["SANDBOX_BASE_URL"]
                etrade = sandbox_etrade
                break
            elif selection == "2":
                base_url = config["DEFAULT"]["PROD_BASE_URL"]
                etrade = prod_etrade
                break
            elif selection == "3":
                break
            else:
                print("Unknown Option Selected!")
        print("")

        request_token, request_token_secret = etrade.get_request_token(
            params={"oauth_callback": "oob", "format": "json"})

        authorize_url = etrade.authorize_url.format(etrade.consumer_key, request_token)
        webbrowser.open(authorize_url)
        text_code = input("Please accept agreement and enter verification code from browser: ")

        session = etrade.get_auth_session(request_token, request_token_secret, params={"oauth_verifier": text_code})

        print(session)
        self.serialize_session(session)
        self.serialize_base_url(base_url)
        return session, base_url

    def serialize_session(self, session: OAuth1Session):
        with open(self.session_file, "wb") as f:
            pickle.dump(session, f)

    def serialize_base_url(self, base_url: str):
        with open(self.base_url_file, "wb") as f:
            pickle.dump(base_url, f)

    @staticmethod
    def deserialize_session(input=DEFAULT_ETRADE_SESSION_FILE) -> OAuth1Session:
        input_file = Path(input)
        with open(input_file, "rb") as f:
            return pickle.load(f)

    @staticmethod
    def deserialize_base_url(input=DEFAULT_ETRADE_BASE_URL_FILE) -> str:
        input_file = Path(input)
        with open(input_file, "rb") as f:
            return pickle.load(f)

    @staticmethod
    def is_file_still_valid(input, max_age=datetime.timedelta(hours=1)):
        input_file = Path(input)
        if not input_file.exists():
            logger.info(f"File {input_file} does not exist")
            return False

        last_modified_unix_timestamp = os.path.getmtime(input_file)
        last_modified = datetime.datetime.fromtimestamp(last_modified_unix_timestamp)
        now = datetime.datetime.now()

        if now - last_modified > max_age:
            return False

        return True


if __name__ == "__main__":
    connector = ETradeConnector(DEFAULT_ETRADE_CONFIG_FILE, DEFAULT_ETRADE_SESSION_FILE)
    session, base_url = connector.establish_connection()
    pass
