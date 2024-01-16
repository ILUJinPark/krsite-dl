from pydantic import BaseModel
from typing import Optional

class Site(BaseModel):
    hostname: str | list[str]
    name: str


class DownloadPayload(BaseModel):
    media: list[str] | list[tuple[str, str]]
    directory: str
    option: Optional[str]


class DataPayload(BaseModel):
    directory_format: list[str]
    media: list[str] | list[tuple[str, str]]
    option: Optional[str]