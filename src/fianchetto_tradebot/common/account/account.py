import logging

logger = logging.getLogger(__name__)


class Account:
    def __init__(self, account_id: str, account_name: str, account_desc: str):
        self.account_id = account_id
        self.account_name = account_name
        self.account_desc = account_desc

    def __str__(self):
        return f"{' - '.join([self.__getattribute__(x) for x in self.__dict__ if self.__getattribute__(x)])}"

    def __repr__(self):
        return self.__str__()