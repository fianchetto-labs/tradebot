import configparser
import logging
import os

from fianchetto_tradebot.common.brokerage.connector import Connector
from fianchetto_tradebot.common.brokerage.etrade.etrade_connector import DEFAULT_SESSION_FILE

config = configparser.ConfigParser()

DEFAULT_IKBR_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.ini')
DEFAULT_IKBR_SESSION_FILE = os.path.join(os.path.dirname(__file__), 'ikbr_session.out')


logger = logging.getLogger(__name__)


class IkbrConnector(Connector):

    def __init__(self, config_file=DEFAULT_IKBR_CONFIG_FILE, session_file=DEFAULT_SESSION_FILE):
        self.config_file = config_file
        self.session_file = session_file

    def get_brokerage(self):
        return "IKBR"


if __name__ == "__main__":
    pass
