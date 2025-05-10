from abc import ABC

from pydantic import BaseModel


class Response(ABC, BaseModel):
    pass