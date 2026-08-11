import hashlib
import json
import logging
from json import JSONDecodeError
from typing import Mapping, Protocol

from fianchetto_tradebot.server.common.brokerage.etrade.credentials import (
    ETradeConnectionCredentials,
    normalize_etrade_base_url,
)


audit_logger = logging.getLogger("fianchetto_tradebot.audit.credentials")


class SecretsManagerClient(Protocol):
    def get_secret_value(self, *, SecretId: str) -> Mapping[str, object]:
        """Return a Secrets Manager secret value response."""

    def put_secret_value(self, *, SecretId: str, SecretString: str) -> object:
        """Store a new Secrets Manager secret string version."""


class ETradeAwsSecretsManagerCredentialProvider:
    """Stores one E*Trade credential document in an existing AWS secret."""

    def __init__(
            self,
            secret_id: str,
            region_name: str | None = None,
            client: SecretsManagerClient | None = None,
            boto3_session: object | None = None):
        if not isinstance(secret_id, str) or not secret_id.strip():
            raise ValueError("E*Trade AWS Secrets Manager secret_id must be a non-empty string")
        self.secret_id = secret_id.strip()
        self._client = client or _build_secrets_manager_client(
            region_name=region_name,
            boto3_session=boto3_session,
        )

    def load(self) -> ETradeConnectionCredentials | None:
        secret = self._load_secret_document()
        if secret is None:
            return None
        return ETradeConnectionCredentials.from_mapping(secret)

    def store(self, credentials: ETradeConnectionCredentials) -> None:
        self._store_secret_document(credentials.to_mapping())

    def load_base_url(self) -> str | None:
        return self._load_string_field("base_url", required=False)

    def store_base_url(self, base_url: str) -> None:
        self._store_secret_field("base_url", normalize_etrade_base_url(base_url, "base_url"))

    def load_request_token(self) -> str:
        return self._load_string_field("request_token")

    def store_request_token(self, token: str) -> None:
        self._store_secret_field("request_token", token)

    def load_request_token_secret(self) -> str:
        return self._load_string_field("request_token_secret")

    def store_request_token_secret(self, token_secret: str) -> None:
        self._store_secret_field("request_token_secret", token_secret)

    def load_oauth_token(self) -> str:
        return self._load_string_field("oauth_token")

    def store_oauth_token(self, token: str) -> None:
        self._store_secret_field("oauth_token", token)

    def load_oauth_token_secret(self) -> str:
        return self._load_string_field("oauth_token_secret")

    def store_oauth_token_secret(self, token_secret: str) -> None:
        self._store_secret_field("oauth_token_secret", token_secret)

    def _load_string_field(self, field: str, required: bool = True) -> str | None:
        secret = self._load_secret_document()
        if secret is None:
            if required:
                raise ValueError(f"E*Trade AWS credential secret does not contain {field}")
            return None

        value = secret.get(field)
        if value is None and not required:
            return None
        if not isinstance(value, str):
            raise ValueError(f"E*Trade AWS credential secret field {field} must be a string")
        return value

    def _store_secret_field(self, field: str, value: str) -> None:
        secret = self._load_secret_document()
        if secret is None:
            raise ValueError("E*Trade AWS credential secret must exist before fields can be updated")
        secret[field] = value
        self._store_secret_document(secret)

    def _load_secret_document(self) -> dict[str, object] | None:
        response = self._get_secret_value()
        if response is None:
            return None

        if "SecretString" not in response:
            raise ValueError("E*Trade AWS credential secret must contain SecretString")

        secret_string = response["SecretString"]
        if not isinstance(secret_string, str):
            raise ValueError("E*Trade AWS credential SecretString must be a string")

        try:
            secret = json.loads(secret_string)
        except JSONDecodeError as exc:
            raise ValueError("E*Trade AWS credential SecretString must be valid JSON") from exc

        if not isinstance(secret, dict):
            raise ValueError("E*Trade AWS credential SecretString must contain a JSON object")

        return secret

    def _get_secret_value(self) -> Mapping[str, object] | None:
        try:
            response = self._client.get_secret_value(SecretId=self.secret_id)
            _log_secret_access("GetSecretValue", "success", self.secret_id)
            return response
        except Exception as exc:
            if _is_resource_not_found_error(exc):
                _log_secret_access("GetSecretValue", "missing", self.secret_id)
                return None
            _log_secret_access("GetSecretValue", "failure", self.secret_id)
            raise RuntimeError("E*Trade AWS credential secret read failed") from None

    def _store_secret_document(self, secret: Mapping[str, object]) -> None:
        try:
            self._client.put_secret_value(
                SecretId=self.secret_id,
                SecretString=json.dumps(secret),
            )
        except Exception:
            _log_secret_access("PutSecretValue", "failure", self.secret_id)
            raise RuntimeError("E*Trade AWS credential secret write failed") from None
        else:
            _log_secret_access("PutSecretValue", "success", self.secret_id)


def _build_secrets_manager_client(
        region_name: str | None,
        boto3_session: object | None) -> SecretsManagerClient:
    if boto3_session is None:
        import boto3

        boto3_session = boto3.session.Session()

    client_args = {"service_name": "secretsmanager"}
    if region_name:
        client_args["region_name"] = region_name
    return boto3_session.client(**client_args)


def _is_resource_not_found_error(exc: Exception) -> bool:
    response = getattr(exc, "response", None)
    if not isinstance(response, Mapping):
        return False
    error = response.get("Error")
    if not isinstance(error, Mapping):
        return False
    return error.get("Code") == "ResourceNotFoundException"


def _log_secret_access(operation: str, outcome: str, secret_id: str) -> None:
    audit_logger.info(
        "E*Trade credential secret access provider=aws_secrets_manager "
        "operation=%s outcome=%s secret_ref=%s",
        operation,
        outcome,
        _secret_reference(secret_id),
    )


def _secret_reference(secret_id: str) -> str:
    return hashlib.sha256(secret_id.encode("utf-8")).hexdigest()[:12]
