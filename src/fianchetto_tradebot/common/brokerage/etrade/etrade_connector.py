import configparser
import datetime
import logging
import os
import pickle
import webbrowser
from pathlib import Path

from aioauth_client import OAuth1Client
from rauth import OAuth1Service, OAuth1Session

from fianchetto_tradebot.common.brokerage.connector import Connector

config = configparser.ConfigParser()

DEFAULT_CONFIG_FILE = os.path.join(os.path.dirname(__file__), './config.ini')

DEFAULT_SESSION_FILE = os.path.join(os.path.dirname(__file__), '/tmp/fianchetto_serialized/etrade_session.out')
DEFAULT_ASYNC_SESSION_FILE = os.path.join(os.path.dirname(__file__), '/tmp/fianchetto_serialized/serialized/async_etrade_session.out')

DEFAULT_ETRADE_BASE_URL_FILE = os.path.join(os.path.dirname(__file__), '/tmp/fianchetto_serialized/etrade_base_url.out')

# For debugging
REQUEST_TOKEN_FILE = os.path.join(os.path.dirname(__file__), '/tmp/fianchetto_serialized/etrade_request_token.out')
REQUEST_TOKEN_SECRET_FILE =os.path.join(os.path.dirname(__file__), '/tmp/fianchetto_serialized/etrade_request_token_secret.out')
OAUTH_TOKEN_FILE = os.path.join(os.path.dirname(__file__), '/tmp/fianchetto_serialized/etrade_oauth_token.out')
OAUTH_TOKEN_SECRET_FILE =os.path.join(os.path.dirname(__file__), '/tmp/fianchetto_serialized/etrade_auth_token_secret.out')

logger = logging.getLogger(__name__)

BROKERAGE_NAME = "E*TRADE"

class ETradeConnector(Connector):
    def __init__(self, config_file=DEFAULT_CONFIG_FILE, session_file=DEFAULT_SESSION_FILE, async_session_file=DEFAULT_ASYNC_SESSION_FILE, base_url_file=DEFAULT_ETRADE_BASE_URL_FILE):
        self.brokerage = BROKERAGE_NAME
        self.config_file = config_file
        self.session_file = session_file
        self.async_session_file = async_session_file
        self.base_url_file = base_url_file
        self.session, self.async_session, self.base_url = self.load_connection()

    def load_base_url(self) -> str:
        persisted_file = self.base_url_file
        if ETradeConnector.is_file_still_valid(persisted_file):
            return ETradeConnector.deserialize_base_url(persisted_file)

        return self.establish_connection()[1]

    def load_connection(self) -> (OAuth1Session, OAuth1Client, str):
        persisted_session_file = self.session_file
        persisted_async_session_file = self.async_session_file
        persisted_base_url_file = self.base_url_file
        if ETradeConnector.is_file_still_valid(persisted_session_file) and ETradeConnector.is_file_still_valid(persisted_base_url_file):
            return (ETradeConnector.deserialize_session(persisted_session_file),
                    ETradeConnector.deserialize_session(persisted_async_session_file),
                    ETradeConnector.deserialize_base_url(persisted_base_url_file))

        return self.establish_connection()

    def establish_connection(self) -> (OAuth1Session, OAuth1Client, str):
        config.read(self.config_file)
        sandbox_oauth1_sync_service = OAuth1Service(
            name="etrade",
            consumer_key=config["SANDBOX"]["SANDBOX_API_KEY"],
            consumer_secret=config["SANDBOX"]["SANDBOX_API_SECRET"],
            request_token_url="https://api.etrade.com/oauth/request_token",
            access_token_url="https://api.etrade.com/oauth/access_token",
            authorize_url="https://us.etrade.com/e/t/etws/authorize?key={}&token={}",
            base_url="https://api.etrade.com")

        prod_oauth1_sync_service = OAuth1Service(
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
                oauth1_sync_service = sandbox_oauth1_sync_service
                break
            elif selection == "2":
                base_url = config["DEFAULT"]["PROD_BASE_URL"]
                oauth1_sync_service = prod_oauth1_sync_service
                break
            elif selection == "3":
                break
            else:
                print("Unknown Option Selected!")
        print("")

        request_token, request_token_secret = oauth1_sync_service.get_request_token(
            params={"oauth_callback": "oob", "format": "json"})

        authorize_url = oauth1_sync_service.authorize_url.format(oauth1_sync_service.consumer_key, request_token)
        webbrowser.open(authorize_url)
        text_code = input("Please accept agreement and enter verification code from browser: ")

        session: OAuth1Session = oauth1_sync_service.get_auth_session(request_token, request_token_secret, params={"oauth_verifier": text_code})

        async_session = OAuth1Client(
            consumer_key=oauth1_sync_service.consumer_key,
            consumer_secret=oauth1_sync_service.consumer_secret,
            resource_owner_key=request_token,
            resource_owner_secret=request_token_secret,
            access_token_key=session.access_token,
            oauth_token=session.access_token,
            oauth_token_secret=session.access_token_secret,
            base_url=base_url,
            signature_method='HMAC-SHA1',
            signature_type="query"
        )

        self.serialize_session(session)
        self.serialize_async_session(async_session)
        self.serialize_request_token(request_token)
        self.serialize_base_url(base_url)

        # For debugging
        self.serialize_request_token_secret(request_token_secret)
        self.serialize_oauth_token(session.access_token)
        self.serialize_oauth_token_secret(session.access_token_secret)

        return session, async_session, base_url

    def serialize_session(self, session: OAuth1Session):
        file_to_serialize = self.session_file
        if not os.path.exists(os.path.dirname(file_to_serialize)):
            try:
                os.makedirs(os.path.dirname(file_to_serialize))
            except Exception as e:
                raise(f"Could not make path for file {file_to_serialize}")
        with open(file_to_serialize, "wb") as f:
            pickle.dump(session, f)

    def serialize_async_session(self, async_session: OAuth1Client):
        file_to_serialize = self.async_session_file
        if not os.path.exists(os.path.dirname(file_to_serialize)):
            try:
                os.makedirs(os.path.dirname(file_to_serialize))
            except Exception as e:
                raise (f"Could not make path for file {file_to_serialize}")
        with open(file_to_serialize, "wb") as f:
            pickle.dump(async_session, f)

    def serialize_request_token(self, token: str):
        file_to_serialize = REQUEST_TOKEN_FILE
        if not os.path.exists(os.path.dirname(file_to_serialize)):
            try:
                os.makedirs(os.path.dirname(file_to_serialize))
            except Exception as e:
                raise (f"Could not make path for file {file_to_serialize}")
        with open(REQUEST_TOKEN_FILE, "wb") as f:
            pickle.dump(token, f)

    def serialize_request_token_secret(self, token_secret: str):
        file_to_serialize = REQUEST_TOKEN_SECRET_FILE
        if not os.path.exists(os.path.dirname(file_to_serialize)):
            try:
                os.makedirs(os.path.dirname(file_to_serialize))
            except Exception:
                raise (f"Could not make path for file {file_to_serialize}")
        with open(REQUEST_TOKEN_SECRET_FILE, "wb") as f:
            pickle.dump(token_secret, f)

    def serialize_oauth_token(self, token: str):
        file_to_serialize = OAUTH_TOKEN_FILE
        if not os.path.exists(os.path.dirname(file_to_serialize)):
            try:
                os.makedirs(os.path.dirname(file_to_serialize))
            except Exception:
                raise (f"Could not make path for file {file_to_serialize}")
        with open(OAUTH_TOKEN_FILE, "wb") as f:
            pickle.dump(token, f)

    def serialize_oauth_token_secret(self, token_secret: str):
        file_to_serialize = OAUTH_TOKEN_SECRET_FILE
        if not os.path.exists(os.path.dirname(file_to_serialize)):
            try:
                os.makedirs(os.path.dirname(file_to_serialize))
            except Exception:
                raise (f"Could not make path for file {file_to_serialize}")
        with open(OAUTH_TOKEN_SECRET_FILE, "wb") as f:
            pickle.dump(token_secret, f)

    def serialize_base_url(self, base_url: str):
        file_to_serialize = self.base_url_file
        if not os.path.exists(os.path.dirname(file_to_serialize)):
            try:
                os.makedirs(os.path.dirname(file_to_serialize))
            except Exception:
                raise (f"Could not make path for file {file_to_serialize}")
        with open(file_to_serialize, "wb") as f:
            pickle.dump(base_url, f)

    @staticmethod
    def deserialize_session(input=DEFAULT_SESSION_FILE) -> OAuth1Session:
        input_file = Path(input)
        with open(input_file, "rb") as f:
            return pickle.load(f)

    @staticmethod
    def deserialize_async_session(input=DEFAULT_ASYNC_SESSION_FILE) -> OAuth1Session:
        input_file = Path(input)
        with open(input_file, "rb") as f:
            return pickle.load(f)

    @staticmethod
    def deserialize_request_token(input=REQUEST_TOKEN_FILE) -> str:
        input_file = Path(input)
        with open(input_file, "rb") as f:
            return pickle.load(f)

    @staticmethod
    def deserialize_request_token_secret(input=REQUEST_TOKEN_SECRET_FILE) -> str:
        input_file = Path(input)
        with open(input_file, "rb") as f:
            return pickle.load(f)

    @staticmethod
    def deserialize_oauth_token(input=OAUTH_TOKEN_FILE) -> str:
        input_file = Path(input)
        with open(input_file, "rb") as f:
            return pickle.load(f)

    @staticmethod
    def deserialize_oauth_token_secret(input=OAUTH_TOKEN_SECRET_FILE) -> str:
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
