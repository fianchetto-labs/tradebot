import csv
import logging
import os

logger = logging.getLogger(__name__)

DEFAULT_KV_FILENAME = os.path.join(os.path.dirname(__file__), './resources/tickers.csv')
NAME_NOT_FOUND = "NOT_FOUND"


class LocalTickerLookup:

    kv = dict()

    @staticmethod
    def lookup(ticker):
        if len(LocalTickerLookup.kv) == 0:
            logger.info("Populating local cache from File")
            LocalTickerLookup.load_cache_from_file()
        if ticker in LocalTickerLookup.kv:
            return LocalTickerLookup.kv[ticker]
        return NAME_NOT_FOUND

    @staticmethod
    def load_cache_from_file(filename=DEFAULT_KV_FILENAME):
        with open(filename) as file:
            output = csv.DictReader(file, delimiter=',')
            for row in output:
                LocalTickerLookup.kv[row["symbol"]] = row["name"]
