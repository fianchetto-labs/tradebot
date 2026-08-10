import datetime
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Protocol
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

REQUIRED_CREDENTIAL_FIELDS = (
    "consumer_key",
    "consumer_secret",
    "access_token",
    "access_token_secret",
    "base_url",
)
OPTIONAL_CREDENTIAL_FIELDS = (
    "request_token",
    "request_token_secret",
)


@dataclass(frozen=True, repr=False)
class ETradeConnectionCredentials:
    consumer_key: str
    consumer_secret: str
    access_token: str
    access_token_secret: str
    request_token: str | None
    request_token_secret: str | None
    base_url: str

    def __repr__(self) -> str:
        return (
            "ETradeConnectionCredentials("
            "consumer_key=<redacted>, "
            "consumer_secret=<redacted>, "
            "access_token=<redacted>, "
            "access_token_secret=<redacted>, "
            "request_token=<redacted>, "
            "request_token_secret=<redacted>, "
            f"base_url={self.base_url!r})"
        )

    @classmethod
    def from_mapping(cls, credentials: Mapping[str, object]) -> "ETradeConnectionCredentials":
        if not isinstance(credentials, Mapping):
            raise ValueError("E*Trade connection credentials must be a JSON object")

        normalized_credentials = dict(credentials)
        for field in REQUIRED_CREDENTIAL_FIELDS:
            _require_non_empty_string(normalized_credentials, field)

        for field in OPTIONAL_CREDENTIAL_FIELDS:
            if field not in normalized_credentials:
                raise ValueError(f"E*Trade connection credentials must include {field}")
            value = normalized_credentials[field]
            if value is not None:
                _require_non_empty_string(normalized_credentials, field)

        return cls(
            consumer_key=normalized_credentials["consumer_key"],
            consumer_secret=normalized_credentials["consumer_secret"],
            access_token=normalized_credentials["access_token"],
            access_token_secret=normalized_credentials["access_token_secret"],
            request_token=normalized_credentials["request_token"],
            request_token_secret=normalized_credentials["request_token_secret"],
            base_url=normalize_etrade_base_url(normalized_credentials["base_url"], "base_url"),
        )

    def to_mapping(self) -> dict[str, str | None]:
        return {
            "consumer_key": self.consumer_key,
            "consumer_secret": self.consumer_secret,
            "access_token": self.access_token,
            "access_token_secret": self.access_token_secret,
            "request_token": self.request_token,
            "request_token_secret": self.request_token_secret,
            "base_url": self.base_url,
        }


class ETradeCredentialProvider(Protocol):
    def load(self) -> ETradeConnectionCredentials | None:
        """Return valid connection credentials, or None when the provider has no usable record."""

    def store(self, credentials: ETradeConnectionCredentials) -> None:
        """Persist connection credentials."""

    def load_base_url(self) -> str | None:
        """Return a standalone base URL fallback, or None when absent or expired."""

    def store_base_url(self, base_url: str) -> None:
        """Persist a standalone base URL fallback."""


class ETradeFileCredentialProvider:
    def __init__(
            self,
            credentials_file: str | os.PathLike[str],
            base_url_file: str | os.PathLike[str],
            max_age: datetime.timedelta):
        self.credentials_file = Path(credentials_file)
        self.base_url_file = Path(base_url_file)
        self.max_age = max_age

    def load(self) -> ETradeConnectionCredentials | None:
        if not is_file_still_valid(self.credentials_file, max_age=self.max_age):
            return None
        return ETradeConnectionCredentials.from_mapping(_deserialize_json_object(self.credentials_file))

    def store(self, credentials: ETradeConnectionCredentials) -> None:
        _serialize_json_object(credentials.to_mapping(), self.credentials_file)

    def load_base_url(self) -> str | None:
        if not is_file_still_valid(self.base_url_file, max_age=self.max_age):
            return None
        return normalize_etrade_base_url(_deserialize_json_value(self.base_url_file), "base_url")

    def store_base_url(self, base_url: str) -> None:
        _serialize_json_value(normalize_etrade_base_url(base_url, "base_url"), self.base_url_file)


def is_file_still_valid(input_file: str | os.PathLike[str], max_age: datetime.timedelta) -> bool:
    path = Path(input_file)
    if not path.exists():
        logger.info("File %s does not exist", path)
        return False

    last_modified_unix_timestamp = os.path.getmtime(path)
    last_modified = datetime.datetime.fromtimestamp(last_modified_unix_timestamp)
    now = datetime.datetime.now()

    if now - last_modified > max_age:
        return False

    return True


def normalize_etrade_base_url(raw_base_url: object, source: str) -> str:
    if not isinstance(raw_base_url, str) or not raw_base_url.strip():
        raise ValueError(f"E*Trade {source} must be a non-empty URL")

    base_url = raw_base_url.strip().rstrip("/")
    parsed_url = urlparse(base_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError(f"E*Trade {source} must be an http(s) URL")

    return base_url


def serialize_connection_credentials(
        credentials: Mapping[str, object],
        output_file: str | os.PathLike[str]) -> None:
    credential_document = ETradeConnectionCredentials.from_mapping(credentials)
    _serialize_json_object(credential_document.to_mapping(), output_file)


def deserialize_connection_credentials(input_file: str | os.PathLike[str]) -> dict[str, object]:
    return _deserialize_json_object(input_file)


def serialize_json_value(value: object, output_file: str | os.PathLike[str]) -> None:
    _serialize_json_value(value, output_file)


def deserialize_json_value(input_file: str | os.PathLike[str]) -> object:
    return _deserialize_json_value(input_file)


def _require_non_empty_string(credentials: Mapping[str, object], field: str) -> None:
    if field not in credentials:
        raise ValueError(f"E*Trade connection credentials must include {field}")
    value = credentials[field]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"E*Trade connection credential {field} must be a non-empty string")


def _serialize_json_value(value: object, output_file: str | os.PathLike[str]) -> None:
    _serialize_json_object({"value": value}, output_file)


def _deserialize_json_value(input_file: str | os.PathLike[str]) -> object:
    with open(Path(input_file)) as f:
        return json.load(f)["value"]


def _serialize_json_object(value: Mapping[str, object], output_file: str | os.PathLike[str]) -> None:
    _ensure_private_parent(output_file)
    with open(Path(output_file), "w") as f:
        json.dump(value, f)
    _chmod_private(output_file)


def _deserialize_json_object(input_file: str | os.PathLike[str]) -> dict[str, object]:
    with open(Path(input_file)) as f:
        return json.load(f)


def _ensure_private_parent(output_file: str | os.PathLike[str]) -> None:
    parent_dir = Path(output_file).parent
    parent_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(parent_dir, 0o700)


def _chmod_private(output_file: str | os.PathLike[str]) -> None:
    os.chmod(output_file, 0o600)
