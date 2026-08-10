import json

import pytest

from fianchetto_tradebot.server.common.brokerage.etrade.aws_credentials import (
    ETradeAwsSecretsManagerCredentialProvider,
)
from fianchetto_tradebot.server.common.brokerage.etrade.credentials import (
    ETradeConnectionCredentials,
)
from tests.fixtures.aws_secrets_manager import FakeSecretsManagerClient


SECRET_ID = "tradebot/etrade/live/operator"


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
