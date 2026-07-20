import json
import stat
from unittest.mock import patch

import pytest
from aioauth_client import OAuth1Client
from rauth import OAuth1Session

from fianchetto_tradebot.server.common.brokerage.etrade.etrade_connector import (
    ETRADE_API_BASE_URL_ENV_VAR,
    ETradeConnector,
)


def test_connector_uses_sensible_fake_credentials_with_simulator_endpoint(tmp_path):
    # Given
    # A fake credential document shaped like the real E*Trade connection cache.
    credentials_file = tmp_path / "connection.json"
    _write_credentials(credentials_file, base_url="http://etrade-sim:8090/")

    # When
    # The connector is constructed with the fake credential document.
    connector = ETradeConnector(
        config_file=str(tmp_path / "missing-config.ini"),
        session_file=str(credentials_file),
        async_session_file=str(credentials_file),
        base_url_file=str(tmp_path / "missing-base-url.json"),
        env={},
    )

    # Then
    # It targets the simulator with the same OAuth-shaped sessions production uses.
    assert connector.base_url == "http://etrade-sim:8090"
    assert connector.load_base_url() == "http://etrade-sim:8090"
    assert isinstance(connector.session, OAuth1Session)
    assert isinstance(connector.async_session, OAuth1Client)


def test_connector_accepts_serialized_session_credentials_without_request_tokens(tmp_path):
    # Given
    # The credential shape produced by serialize_session for an already-authorized session.
    credentials_file = tmp_path / "connection.json"
    _write_credentials(
        credentials_file,
        base_url="http://etrade-sim:8090",
        request_token=None,
        request_token_secret=None,
    )

    # When
    # The connector rebuilds the sessions.
    connector = ETradeConnector(
        config_file=str(tmp_path / "missing-config.ini"),
        session_file=str(credentials_file),
        async_session_file=str(credentials_file),
        base_url_file=str(tmp_path / "missing-base-url.json"),
        env={},
    )

    # Then
    # Required credential fields are still validated while legacy request-token values remain optional.
    assert connector.base_url == "http://etrade-sim:8090"
    assert connector.async_session.oauth_token == "simulator-access-token"


def test_connector_env_base_url_overrides_stored_credential_endpoint(tmp_path):
    # Given
    # Valid OAuth-shaped credentials from one endpoint and an explicit runtime endpoint override.
    credentials_file = tmp_path / "connection.json"
    _write_credentials(credentials_file, base_url="https://api.etrade.com")

    # When
    # The connector is created with an environment base URL override.
    connector = ETradeConnector(
        session_file=str(credentials_file),
        async_session_file=str(credentials_file),
        base_url_file=str(tmp_path / "base-url.json"),
        env={ETRADE_API_BASE_URL_ENV_VAR: "http://localhost:8090/"},
    )

    # Then
    # The stored credentials are reused, but service calls target the configured endpoint.
    assert connector.base_url == "http://localhost:8090"
    assert connector.async_session.base_url == "http://localhost:8090"
    assert stat.S_IMODE(credentials_file.stat().st_mode) == 0o600


def test_base_url_precedence_is_env_then_credentials_then_standalone_file(tmp_path):
    # Given
    # All supported base-url sources exist.
    credentials_file = tmp_path / "connection.json"
    standalone_base_url_file = tmp_path / "base-url.json"
    _write_credentials(credentials_file, base_url="https://credential-cache.example.test")
    _write_standalone_base_url(standalone_base_url_file, "https://standalone.example.test")

    # When / Then
    # Runtime configuration takes precedence over cached credential and legacy standalone values.
    assert _connector_for_base_url_resolution(
        credentials_file=credentials_file,
        standalone_base_url_file=standalone_base_url_file,
        env={ETRADE_API_BASE_URL_ENV_VAR: "http://etrade-sim:8090"},
    ).load_base_url() == "http://etrade-sim:8090"

    # When / Then
    # Credential-cache base URL wins when runtime configuration is absent.
    assert _connector_for_base_url_resolution(
        credentials_file=credentials_file,
        standalone_base_url_file=standalone_base_url_file,
        env={},
    ).load_base_url() == "https://credential-cache.example.test"

    # When / Then
    # The legacy standalone base-url file is a final cached fallback.
    assert _connector_for_base_url_resolution(
        credentials_file=tmp_path / "missing-connection.json",
        standalone_base_url_file=standalone_base_url_file,
        env={},
    ).load_base_url() == "https://standalone.example.test"


def test_connector_rejects_missing_required_credential_field(tmp_path):
    credentials_file = tmp_path / "connection.json"
    credentials = _credentials_dict()
    del credentials["consumer_key"]

    with pytest.raises(ValueError, match="consumer_key"):
        ETradeConnector._serialize_connection_credentials(credentials, credentials_file)


def test_connector_rejects_blank_credential_value(tmp_path):
    credentials_file = tmp_path / "connection.json"
    credentials = _credentials_dict(access_token=" ")

    with pytest.raises(ValueError, match="access_token"):
        ETradeConnector._serialize_connection_credentials(credentials, credentials_file)


def test_connector_rejects_invalid_credential_base_url(tmp_path):
    credentials_file = tmp_path / "connection.json"
    credentials = _credentials_dict(base_url="etrade-sim:8090")

    with pytest.raises(ValueError, match="http\\(s\\) URL"):
        ETradeConnector._serialize_connection_credentials(credentials, credentials_file)


def test_connector_rejects_manually_authored_invalid_credential_file(tmp_path):
    credentials_file = tmp_path / "connection.json"
    credentials_file.write_text(json.dumps(_credentials_dict(access_token="")))

    with pytest.raises(ValueError, match="access_token"):
        ETradeConnector._build_connection_from_credentials_file(credentials_file)


def test_connector_rejects_invalid_env_base_url(tmp_path):
    credentials_file = tmp_path / "connection.json"
    _write_credentials(credentials_file, base_url="http://etrade-sim:8090")

    with pytest.raises(ValueError, match=ETRADE_API_BASE_URL_ENV_VAR):
        ETradeConnector(
            session_file=str(credentials_file),
            async_session_file=str(credentials_file),
            base_url_file=str(tmp_path / "base-url.json"),
            env={ETRADE_API_BASE_URL_ENV_VAR: "etrade-sim:8090"},
        )


def test_connector_rejects_invalid_standalone_base_url_file(tmp_path):
    connector = object.__new__(ETradeConnector)
    connector.base_url_file = str(tmp_path / "base-url.json")

    with pytest.raises(ValueError, match="http\\(s\\) URL"):
        connector.serialize_base_url("etrade-sim:8090")


def test_configured_endpoint_does_not_skip_credentials(tmp_path):
    # Given
    # An endpoint override but no credential document.
    env = {ETRADE_API_BASE_URL_ENV_VAR: "http://etrade-sim:8090"}

    # When / Then
    # The connector still falls through to the normal connection establishment path.
    with patch.object(ETradeConnector, "establish_connection", side_effect=RuntimeError("credentials required")):
        with pytest.raises(RuntimeError, match="credentials required"):
            ETradeConnector(
                config_file=str(tmp_path / "missing-config.ini"),
                session_file=str(tmp_path / "missing-connection.json"),
                async_session_file=str(tmp_path / "missing-connection.json"),
                base_url_file=str(tmp_path / "missing-base-url.json"),
                env=env,
            )


def _write_credentials(credentials_file, **overrides) -> None:
    connector = object.__new__(ETradeConnector)
    connector.credentials_file = str(credentials_file)
    connector.serialize_connection_credentials(**_credentials_dict(**overrides))


def _write_standalone_base_url(base_url_file, base_url: str) -> None:
    connector = object.__new__(ETradeConnector)
    connector.base_url_file = str(base_url_file)
    connector.serialize_base_url(base_url)


def _connector_for_base_url_resolution(credentials_file, standalone_base_url_file, env) -> ETradeConnector:
    connector = object.__new__(ETradeConnector)
    connector.credentials_file = str(credentials_file)
    connector.base_url_file = str(standalone_base_url_file)
    connector.env = env
    return connector


def _credentials_dict(**overrides) -> dict:
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
