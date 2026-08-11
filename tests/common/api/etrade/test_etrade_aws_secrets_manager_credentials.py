import hashlib
import json
import logging

import pytest

from fianchetto_tradebot.server.common.brokerage.etrade.aws_credentials import (
    ETradeAwsSecretsManagerCredentialProvider,
)
from fianchetto_tradebot.server.common.brokerage.etrade.credentials import (
    ETradeConnectionCredentials,
)
from tests.fixtures.aws_secrets_manager import FakeSecretsManagerClient


SECRET_ID = "tradebot/etrade/live/operator"
AUDIT_LOGGER_NAME = "fianchetto_tradebot.audit.credentials"


def test_aws_provider_loads_connection_credentials_from_secret_string():
    # Given
    # An existing Secrets Manager secret containing the E*Trade credential document.
    client = FakeSecretsManagerClient({
        SECRET_ID: json.dumps(_credentials_dict(base_url="https://api.etrade.com/")),
    })
    provider = ETradeAwsSecretsManagerCredentialProvider(secret_id=SECRET_ID, client=client)

    # When
    # The provider loads the credential document through the AWS-shaped client boundary.
    credentials = provider.load()

    # Then
    # The same domain validation and normalization used by local credentials still applies.
    assert credentials == ETradeConnectionCredentials.from_mapping(
        _credentials_dict(base_url="https://api.etrade.com")
    )
    assert client.get_secret_value_calls == [SECRET_ID]


def test_aws_provider_stores_connection_credentials_as_secret_string():
    # Given
    # A pre-created Secrets Manager secret and validated E*Trade credentials.
    client = FakeSecretsManagerClient({SECRET_ID: json.dumps(_credentials_dict())})
    provider = ETradeAwsSecretsManagerCredentialProvider(secret_id=SECRET_ID, client=client)
    credentials = ETradeConnectionCredentials.from_mapping(
        _credentials_dict(base_url="http://etrade-simulator:8090/")
    )

    # When
    # The full connection credential document is stored.
    provider.store(credentials)

    # Then
    # The AWS boundary receives one SecretString JSON document, not local sidecar files.
    assert len(client.put_secret_value_calls) == 1
    assert client.put_secret_value_calls[0][0] == SECRET_ID
    assert client.secret_document(SECRET_ID) == credentials.to_mapping()


def test_aws_provider_updates_base_url_inside_existing_secret_document():
    # Given
    # A full existing credential document in Secrets Manager.
    client = FakeSecretsManagerClient({SECRET_ID: json.dumps(_credentials_dict())})
    provider = ETradeAwsSecretsManagerCredentialProvider(secret_id=SECRET_ID, client=client)

    # When
    # The provider updates the runtime endpoint metadata.
    provider.store_base_url("http://etrade-simulator:8090/")

    # Then
    # The base URL is normalized and the other secret fields are preserved.
    assert provider.load_base_url() == "http://etrade-simulator:8090"
    document = client.secret_document(SECRET_ID)
    assert document["base_url"] == "http://etrade-simulator:8090"
    assert document["consumer_secret"] == "simulator-consumer-secret"


def test_aws_provider_updates_legacy_token_fields_inside_existing_secret_document():
    # Given
    # A full existing credential document in Secrets Manager.
    client = FakeSecretsManagerClient({SECRET_ID: json.dumps(_credentials_dict())})
    provider = ETradeAwsSecretsManagerCredentialProvider(secret_id=SECRET_ID, client=client)

    # When
    # Legacy OAuth token fields are written through the provider.
    provider.store_request_token("updated-request-token")
    provider.store_request_token_secret("updated-request-token-secret")
    provider.store_oauth_token("updated-oauth-token")
    provider.store_oauth_token_secret("updated-oauth-token-secret")

    # Then
    # They are persisted in the same AWS secret document and round-trip as strings.
    assert provider.load_request_token() == "updated-request-token"
    assert provider.load_request_token_secret() == "updated-request-token-secret"
    assert provider.load_oauth_token() == "updated-oauth-token"
    assert provider.load_oauth_token_secret() == "updated-oauth-token-secret"


def test_aws_provider_returns_none_when_secret_does_not_exist():
    # Given
    # A provider pointing at a missing AWS secret.
    provider = ETradeAwsSecretsManagerCredentialProvider(
        secret_id=SECRET_ID,
        client=FakeSecretsManagerClient(),
    )

    # When / Then
    # Missing cloud state is treated like an absent local credential cache.
    assert provider.load() is None
    assert provider.load_base_url() is None


def test_aws_provider_rejects_malformed_secret_string_without_exposing_value():
    # Given
    # A secret whose payload is not valid JSON.
    client = FakeSecretsManagerClient({SECRET_ID: "not-json-with-simulator-consumer-secret"})
    provider = ETradeAwsSecretsManagerCredentialProvider(secret_id=SECRET_ID, client=client)

    # When / Then
    # The failure explains the shape problem without printing the secret payload.
    with pytest.raises(ValueError) as exc_info:
        provider.load()
    assert "valid JSON" in str(exc_info.value)
    assert "simulator-consumer-secret" not in str(exc_info.value)


def test_aws_provider_rejects_secret_without_secret_string():
    # Given
    # An AWS response containing binary secret material instead of a JSON string.
    class BinarySecretClient(FakeSecretsManagerClient):
        def get_secret_value(self, *, SecretId: str) -> dict[str, object]:
            return {"SecretBinary": b"opaque"}

    provider = ETradeAwsSecretsManagerCredentialProvider(
        secret_id=SECRET_ID,
        client=BinarySecretClient(),
    )

    # When / Then
    # The provider fails closed instead of trying to parse an unsupported secret shape.
    with pytest.raises(ValueError, match="SecretString"):
        provider.load()


def test_aws_provider_rejects_blank_secret_id():
    # Given / When / Then
    # The provider requires a stable configured AWS secret identifier.
    with pytest.raises(ValueError, match="secret_id"):
        ETradeAwsSecretsManagerCredentialProvider(secret_id=" ", client=FakeSecretsManagerClient())


def test_aws_provider_requires_existing_secret_before_field_updates():
    # Given
    # A provider pointing at a missing AWS secret.
    provider = ETradeAwsSecretsManagerCredentialProvider(
        secret_id=SECRET_ID,
        client=FakeSecretsManagerClient(),
    )

    # When / Then
    # Incremental updates do not silently create partial credential documents.
    with pytest.raises(ValueError, match="must exist"):
        provider.store_base_url("http://etrade-simulator:8090")


def test_aws_provider_builds_secrets_manager_client_from_boto3_session():
    # Given
    # A boto3-shaped session object and a configured AWS region.
    class FakeBoto3Session:
        def __init__(self):
            self.client_args = None
            self.client_kwargs = None

        def client(self, *args, **kwargs) -> FakeSecretsManagerClient:
            self.client_args = args
            self.client_kwargs = kwargs
            return FakeSecretsManagerClient({
                SECRET_ID: json.dumps(_credentials_dict()),
            })

    boto3_session = FakeBoto3Session()

    # When
    # The provider owns client construction.
    provider = ETradeAwsSecretsManagerCredentialProvider(
        secret_id=SECRET_ID,
        region_name="us-east-1",
        boto3_session=boto3_session,
    )

    # Then
    # It requests the AWS Secrets Manager client for the configured region.
    assert provider.load() == ETradeConnectionCredentials.from_mapping(_credentials_dict())
    assert boto3_session.client_args == ()
    assert boto3_session.client_kwargs == {
        "service_name": "secretsmanager",
        "region_name": "us-east-1",
    }


def test_aws_provider_logs_safe_secret_read_audit_metadata(caplog):
    # Given
    # An AWS credential provider with a secret containing fake credential material.
    caplog.set_level(logging.INFO, logger=AUDIT_LOGGER_NAME)
    client = FakeSecretsManagerClient({SECRET_ID: json.dumps(_credentials_dict())})
    provider = ETradeAwsSecretsManagerCredentialProvider(secret_id=SECRET_ID, client=client)

    # When
    # The provider reads the secret document.
    provider.load()

    # Then
    # The audit log identifies the operation without printing the secret id or values.
    assert "operation=GetSecretValue" in caplog.text
    assert "outcome=success" in caplog.text
    assert f"secret_ref={_expected_secret_reference(SECRET_ID)}" in caplog.text
    _assert_no_secret_material_was_logged(caplog.text)


def test_aws_provider_logs_safe_secret_write_audit_metadata(caplog):
    # Given
    # An AWS credential provider with a pre-created secret.
    caplog.set_level(logging.INFO, logger=AUDIT_LOGGER_NAME)
    client = FakeSecretsManagerClient({SECRET_ID: json.dumps(_credentials_dict())})
    provider = ETradeAwsSecretsManagerCredentialProvider(secret_id=SECRET_ID, client=client)

    # When
    # The provider writes a new secret version.
    provider.store(ETradeConnectionCredentials.from_mapping(_credentials_dict()))

    # Then
    # The audit log records the write without printing the secret id or payload.
    assert "operation=PutSecretValue" in caplog.text
    assert "outcome=success" in caplog.text
    assert f"secret_ref={_expected_secret_reference(SECRET_ID)}" in caplog.text
    _assert_no_secret_material_was_logged(caplog.text)


def test_aws_provider_logs_missing_secret_without_leaking_secret_id(caplog):
    # Given
    # An AWS credential provider pointing at absent cloud state.
    caplog.set_level(logging.INFO, logger=AUDIT_LOGGER_NAME)
    provider = ETradeAwsSecretsManagerCredentialProvider(
        secret_id=SECRET_ID,
        client=FakeSecretsManagerClient(),
    )

    # When
    # The provider checks for credentials.
    assert provider.load() is None

    # Then
    # Missing state is auditable without exposing the configured secret name.
    assert "operation=GetSecretValue" in caplog.text
    assert "outcome=missing" in caplog.text
    assert f"secret_ref={_expected_secret_reference(SECRET_ID)}" in caplog.text
    _assert_no_secret_material_was_logged(caplog.text)


def test_aws_provider_logs_secret_read_failure_without_exception_payload(caplog):
    # Given
    # A Secrets Manager client that fails with a non-missing upstream error.
    class FailingReadClient(FakeSecretsManagerClient):
        def get_secret_value(self, *, SecretId: str) -> dict[str, object]:
            raise RuntimeError("upstream included simulator-consumer-secret")

    caplog.set_level(logging.INFO, logger=AUDIT_LOGGER_NAME)
    provider = ETradeAwsSecretsManagerCredentialProvider(
        secret_id=SECRET_ID,
        client=FailingReadClient(),
    )

    # When / Then
    # The provider raises a scrubbed operation-level failure and keeps the audit line clean.
    with pytest.raises(RuntimeError) as exc_info:
        provider.load()
    assert str(exc_info.value) == "E*Trade AWS credential secret read failed"
    assert "simulator-consumer-secret" not in str(exc_info.value)
    assert "operation=GetSecretValue" in caplog.text
    assert "outcome=failure" in caplog.text
    _assert_no_secret_material_was_logged(caplog.text)


def test_aws_provider_logs_secret_write_failure_without_secret_payload(caplog):
    # Given
    # A Secrets Manager client that rejects writes after seeing the payload.
    class FailingWriteClient(FakeSecretsManagerClient):
        def put_secret_value(self, *, SecretId: str, SecretString: str) -> dict[str, object]:
            raise RuntimeError("write failed for secret payload")

    caplog.set_level(logging.INFO, logger=AUDIT_LOGGER_NAME)
    client = FailingWriteClient({SECRET_ID: json.dumps(_credentials_dict())})
    provider = ETradeAwsSecretsManagerCredentialProvider(secret_id=SECRET_ID, client=client)

    # When / Then
    # The write failure is auditable without logging the credential payload.
    with pytest.raises(RuntimeError) as exc_info:
        provider.store(ETradeConnectionCredentials.from_mapping(_credentials_dict()))
    assert str(exc_info.value) == "E*Trade AWS credential secret write failed"
    assert "simulator-consumer-secret" not in str(exc_info.value)
    assert "operation=PutSecretValue" in caplog.text
    assert "outcome=failure" in caplog.text
    _assert_no_secret_material_was_logged(caplog.text)


def _credentials_dict(**overrides) -> dict[str, object]:
    credentials = {
        "consumer_key": "simulator-consumer-key",
        "consumer_secret": "simulator-consumer-secret",
        "access_token": "simulator-access-token",
        "access_token_secret": "simulator-access-token-secret",
        "request_token": "simulator-request-token",
        "request_token_secret": "simulator-request-token-secret",
        "base_url": "http://etrade-sim:8090",
    }
    credentials.update(overrides)
    return credentials


def _assert_no_secret_material_was_logged(log_text: str) -> None:
    assert SECRET_ID not in log_text
    assert "simulator-consumer-key" not in log_text
    assert "simulator-consumer-secret" not in log_text
    assert "simulator-access-token" not in log_text
    assert "simulator-access-token-secret" not in log_text
    assert "simulator-request-token" not in log_text
    assert "simulator-request-token-secret" not in log_text


def _expected_secret_reference(secret_id: str) -> str:
    return hashlib.sha256(secret_id.encode("utf-8")).hexdigest()[:12]
