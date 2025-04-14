from abc import ABC

from pydantic import BaseModel


class Request(ABC, BaseModel):
    pass