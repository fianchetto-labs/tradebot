import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Account(BaseModel):
    account_id: str
    account_name: str
    account_desc: str

    def __str__(self):
        return f"{' - '.join([self.__getattribute__(x) for x in self.__dict__ if self.__getattribute__(x)])}"

    def __repr__(self):
        return self.__str__()