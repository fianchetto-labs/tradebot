import json
from pathlib import Path


POLICY_DIR = Path("deploy/aws/credential-custody")
RUNTIME_POLICY = POLICY_DIR / "etrade-runtime-secret-policy.json"
KMS_KEY_POLICY = POLICY_DIR / "etrade-credential-kms-key-policy.json"


def test_runtime_policy_scopes_secret_and_kms_access():
    # Given
    # The runtime IAM policy template for hosted E*Trade credential custody.
    policy = _load_policy(RUNTIME_POLICY)

    # When
    # The policy statements are inspected.
    secret_statement = _statement(policy, "ReadAndUpdateOneEtradeCredentialSecret")
    kms_statement = _statement(policy, "UseCredentialKmsKeyThroughSecretsManager")

    # Then
    # Runtime access is limited to the intended secret, key, and Secrets Manager path.
    assert secret_statement["Action"] == [
        "secretsmanager:DescribeSecret",
        "secretsmanager:GetSecretValue",
        "secretsmanager:PutSecretValue",
    ]
    assert secret_statement["Resource"] == (
        "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:"
        "secret:${TRADEBOT_ETRADE_SECRET_NAME}-*"
    )
    assert kms_statement["Resource"] == (
        "arn:aws:kms:${AWS_REGION}:${AWS_ACCOUNT_ID}:key/${TRADEBOT_CREDENTIAL_KMS_KEY_ID}"
    )
    assert kms_statement["Condition"]["StringEquals"]["kms:ViaService"] == (
        "secretsmanager.${AWS_REGION}.amazonaws.com"
    )
    assert kms_statement["Condition"]["StringLike"]["kms:EncryptionContext:SecretARN"] == (
        secret_statement["Resource"]
    )


def test_runtime_policy_does_not_grant_secret_or_kms_administration():
    # Given
    # The runtime IAM policy template for the TradeBot service role.
    policy = _load_policy(RUNTIME_POLICY)

    # When
    # All runtime actions and resources are inspected.
    actions = {
        action
        for statement in policy["Statement"]
        for action in _as_list(statement["Action"])
    }
    resources = [statement["Resource"] for statement in policy["Statement"]]

    # Then
    # The service cannot enumerate, create, delete, or broadly administer secrets or keys.
    assert "secretsmanager:*" not in actions
    assert "secretsmanager:CreateSecret" not in actions
    assert "secretsmanager:DeleteSecret" not in actions
    assert "secretsmanager:ListSecrets" not in actions
    assert "secretsmanager:PutResourcePolicy" not in actions
    assert "kms:*" not in actions
    assert all(resource != "*" for resource in resources)


def test_kms_key_policy_keeps_admin_and_runtime_roles_separate():
    # Given
    # The KMS key policy template for the credential key.
    policy = _load_policy(KMS_KEY_POLICY)

    # When
    # The admin and runtime statements are inspected.
    admin_statement = _statement(policy, "AllowCredentialAdminsToManageKey")
    runtime_statement = _statement(policy, "AllowRuntimeRoleToUseKeyThroughSecretsManager")

    # Then
    # The admin role manages the key, while the runtime role performs data-key operations.
    assert admin_statement["Principal"]["AWS"] == "${TRADEBOT_CREDENTIAL_ADMIN_ROLE_ARN}"
    assert runtime_statement["Principal"]["AWS"] == "${TRADEBOT_RUNTIME_ROLE_ARN}"
    assert "kms:Decrypt" not in admin_statement["Action"]
    assert "kms:GenerateDataKey" not in admin_statement["Action"]
    assert runtime_statement["Action"] == [
        "kms:Decrypt",
        "kms:DescribeKey",
        "kms:Encrypt",
        "kms:GenerateDataKey",
    ]


def test_kms_runtime_access_is_constrained_to_secrets_manager():
    # Given
    # The KMS key policy template for the credential key.
    policy = _load_policy(KMS_KEY_POLICY)

    # When
    # Runtime key-use conditions are inspected.
    runtime_statement = _statement(policy, "AllowRuntimeRoleToUseKeyThroughSecretsManager")

    # Then
    # The runtime role cannot use the key directly outside Secrets Manager.
    assert runtime_statement["Condition"]["StringEquals"]["kms:ViaService"] == (
        "secretsmanager.${AWS_REGION}.amazonaws.com"
    )
    assert runtime_statement["Condition"]["StringLike"]["kms:EncryptionContext:SecretARN"] == (
        "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:"
        "secret:${TRADEBOT_ETRADE_SECRET_NAME}-*"
    )


def _load_policy(path: Path) -> dict:
    with open(path) as policy_file:
        return json.load(policy_file)


def _statement(policy: dict, sid: str) -> dict:
    for statement in policy["Statement"]:
        if statement["Sid"] == sid:
            return statement
    raise AssertionError(f"Missing policy statement {sid}")


def _as_list(value) -> list:
    if isinstance(value, list):
        return value
    return [value]
