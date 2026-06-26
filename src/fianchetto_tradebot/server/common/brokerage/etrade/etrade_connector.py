import configparser
import datetime
import json
import logging
import os
import webbrowser
from pathlib import Path

from aioauth_client import OAuth1Client
from rauth import OAuth1Service, OAuth1Session

from fianchetto_tradebot.server.common.brokerage.connector import Connector

config = configparser.ConfigParser()

DEFAULT_CONFIG_FILE = os.path.join(os.path.dirname(__file__), './config.ini')

BROKERAGE_NAME = "ETRADE"
BROKERAGE_DIR = "etrade"
DEFAULT_STATE_DIR = os.path.join(os.path.expanduser("~"), ".fianchetto_tradebot")
STATE_DIR = os.environ.get("FIANCHETTO_TRADEBOT_STATE_DIR", DEFAULT_STATE_DIR)
BROKERAGE_STATE_DIR = os.path.join(STATE_DIR, BROKERAGE_DIR)

# TODO: Generalize this across all exchanges
DEFAULT_CREDENTIALS_FILE = os.path.join(BROKERAGE_STATE_DIR, "connection.json")
DEFAULT_SESSION_FILE = DEFAULT_CREDENTIALS_FILE
DEFAULT_ASYNC_SESSION_FILE = DEFAULT_CREDENTIALS_FILE
DEFAULT_ETRADE_BASE_URL_FILE = os.path.join(BROKERAGE_STATE_DIR, "base_url.json")

# For debugging
REQUEST_TOKEN_FILE = os.path.join(BROKERAGE_STATE_DIR, "request_token.json")
REQUEST_TOKEN_SECRET_FILE = os.path.join(BROKERAGE_STATE_DIR, "request_token_secret.json")
OAUTH_TOKEN_FILE = os.path.join(BROKERAGE_STATE_DIR, "oauth_token.json")
OAUTH_TOKEN_SECRET_FILE = os.path.join(BROKERAGE_STATE_DIR, "oauth_token_secret.json")

logger = logging.getLogger(__name__)


class ETradeConnector(Connector):
    def __init__(self, config_file=DEFAULT_CONFIG_FILE, session_file=DEFAULT_SESSION_FILE, async_session_file=DEFAULT_ASYNC_SESSION_FILE, base_url_file=DEFAULT_ETRADE_BASE_URL_FILE):
        self.brokerage = BROKERAGE_NAME
        self.config_file = config_file
        # session_file/async_session_file are kept as constructor aliases for older callers.
        self.credentials_file = session_file
        self.session_file = session_file
        self.async_session_file = async_session_file
        self.base_url_file = base_url_file
        self.session, self.async_session, self.base_url = self.load_connection()

    def load_base_url(self) -> str:
        if ETradeConnector.is_file_still_valid(self.credentials_file):
            return ETradeConnector._deserialize_connection_credentials(self.credentials_file)["base_url"]

        if ETradeConnector.is_file_still_valid(self.base_url_file):
            return ETradeConnector.deserialize_base_url(self.base_url_file)

        return self.establish_connection()[2]

    def load_connection(self) -> (OAuth1Session, OAuth1Client, str):
        if ETradeConnector.is_file_still_valid(self.credentials_file):
            return ETradeConnector._build_connection_from_credentials_file(self.credentials_file)

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

        self.serialize_connection_credentials(
            consumer_key=oauth1_sync_service.consumer_key,
            consumer_secret=oauth1_sync_service.consumer_secret,
            access_token=session.access_token,
            access_token_secret=session.access_token_secret,
            request_token=request_token,
            request_token_secret=request_token_secret,
            base_url=base_url,
        )
        self.serialize_base_url(base_url)

        return session, async_session, base_url

    def serialize_session(self, session: OAuth1Session):
        ETradeConnector._serialize_connection_credentials({
            "consumer_key": session.consumer_key,
            "consumer_secret": session.consumer_secret,
            "access_token": session.access_token,
            "access_token_secret": session.access_token_secret,
            "request_token": None,
            "request_token_secret": None,
            "base_url": self.base_url,
        }, self.credentials_file)

    def serialize_async_session(self, async_session: OAuth1Client):
        # Async sessions are reconstructed from the same credential document as sync sessions.
        return None

    def serialize_connection_credentials(self, consumer_key: str, consumer_secret: str, access_token: str,
                                         access_token_secret: str, request_token: str,
                                         request_token_secret: str, base_url: str):
        ETradeConnector._serialize_connection_credentials({
            "consumer_key": consumer_key,
            "consumer_secret": consumer_secret,
            "access_token": access_token,
            "access_token_secret": access_token_secret,
            "request_token": request_token,
            "request_token_secret": request_token_secret,
            "base_url": base_url,
        }, self.credentials_file)

    def serialize_request_token(self, token: str):
        ETradeConnector._serialize_json_value(token, REQUEST_TOKEN_FILE)

    def serialize_request_token_secret(self, token_secret: str):
        ETradeConnector._serialize_json_value(token_secret, REQUEST_TOKEN_SECRET_FILE)

    def serialize_oauth_token(self, token: str):
        ETradeConnector._serialize_json_value(token, OAUTH_TOKEN_FILE)

    def serialize_oauth_token_secret(self, token_secret: str):
        ETradeConnector._serialize_json_value(token_secret, OAUTH_TOKEN_SECRET_FILE)

    def serialize_base_url(self, base_url: str):
        ETradeConnector._serialize_json_value(base_url, self.base_url_file)

    @staticmethod
    def deserialize_session(input=DEFAULT_SESSION_FILE) -> OAuth1Session:
        return ETradeConnector._build_connection_from_credentials_file(input)[0]

    @staticmethod
    def deserialize_async_session(input=DEFAULT_ASYNC_SESSION_FILE) -> OAuth1Session:
        return ETradeConnector._build_connection_from_credentials_file(input)[1]

    @staticmethod
    def deserialize_request_token(input=REQUEST_TOKEN_FILE) -> str:
        return ETradeConnector._deserialize_json_value(input)

    @staticmethod
    def deserialize_request_token_secret(input=REQUEST_TOKEN_SECRET_FILE) -> str:
        return ETradeConnector._deserialize_json_value(input)

    @staticmethod
    def deserialize_oauth_token(input=OAUTH_TOKEN_FILE) -> str:
        return ETradeConnector._deserialize_json_value(input)

    @staticmethod
    def deserialize_oauth_token_secret(input=OAUTH_TOKEN_SECRET_FILE) -> str:
        return ETradeConnector._deserialize_json_value(input)

    @staticmethod
    def deserialize_base_url(input=DEFAULT_ETRADE_BASE_URL_FILE) -> str:
        return ETradeConnector._deserialize_json_value(input)

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

    @staticmethod
    def _serialize_json_value(value, output_file):
        ETradeConnector._ensure_private_parent(output_file)
        with open(output_file, "w") as f:
            json.dump({"value": value}, f)
        ETradeConnector._chmod_private(output_file)

    @staticmethod
    def _deserialize_json_value(input_file) -> str:
        with open(Path(input_file)) as f:
            return json.load(f)["value"]

    @staticmethod
    def _serialize_connection_credentials(credentials: dict, output_file):
        ETradeConnector._ensure_private_parent(output_file)
        with open(output_file, "w") as f:
            json.dump(credentials, f)
        ETradeConnector._chmod_private(output_file)

    @staticmethod
    def _deserialize_connection_credentials(input_file) -> dict:
        with open(Path(input_file)) as f:
            return json.load(f)

    @staticmethod
    def _build_connection_from_credentials_file(input_file) -> (OAuth1Session, OAuth1Client, str):
        credentials = ETradeConnector._deserialize_connection_credentials(input_file)
        base_url = credentials["base_url"]

        service = OAuth1Service(
            name="etrade",
            consumer_key=credentials["consumer_key"],
            consumer_secret=credentials["consumer_secret"],
            request_token_url="https://api.etrade.com/oauth/request_token",
            access_token_url="https://api.etrade.com/oauth/access_token",
            authorize_url="https://us.etrade.com/e/t/etws/authorize?key={}&token={}",
            base_url="https://api.etrade.com")

        session = OAuth1Session(
            consumer_key=credentials["consumer_key"],
            consumer_secret=credentials["consumer_secret"],
            access_token=credentials["access_token"],
            access_token_secret=credentials["access_token_secret"],
            service=service)

        async_session = OAuth1Client(
            consumer_key=credentials["consumer_key"],
            consumer_secret=credentials["consumer_secret"],
            resource_owner_key=credentials["request_token"],
            resource_owner_secret=credentials["request_token_secret"],
            access_token_key=credentials["access_token"],
            oauth_token=credentials["access_token"],
            oauth_token_secret=credentials["access_token_secret"],
            base_url=base_url,
            signature_method='HMAC-SHA1',
            signature_type="query")

        return session, async_session, base_url

    @staticmethod
    def _ensure_private_parent(output_file):
        parent_dir = os.path.dirname(output_file)
        os.makedirs(parent_dir, mode=0o700, exist_ok=True)
        os.chmod(parent_dir, 0o700)

    @staticmethod
    def _chmod_private(output_file):
        os.chmod(output_file, 0o600)
