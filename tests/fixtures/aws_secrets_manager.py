import json


class FakeResourceNotFound(Exception):
    def __init__(self, secret_id: str):
        super().__init__(f"Secret does not exist: {secret_id}")
        self.response = {"Error": {"Code": "ResourceNotFoundException"}}


class FakeSecretsManagerClient:
    def __init__(self, secrets: dict[str, str] | None = None):
        self.secrets = secrets or {}
        self.get_secret_value_calls: list[str] = []
        self.put_secret_value_calls: list[tuple[str, str]] = []

    def get_secret_value(self, *, SecretId: str) -> dict[str, object]:
        self.get_secret_value_calls.append(SecretId)
        if SecretId not in self.secrets:
            raise FakeResourceNotFound(SecretId)
        return {"SecretString": self.secrets[SecretId]}

    def put_secret_value(self, *, SecretId: str, SecretString: str) -> dict[str, object]:
        self.put_secret_value_calls.append((SecretId, SecretString))
        if SecretId not in self.secrets:
            raise FakeResourceNotFound(SecretId)
        self.secrets[SecretId] = SecretString
        return {"VersionId": "fake-version-id"}

    def secret_document(self, secret_id: str) -> dict[str, object]:
        return json.loads(self.secrets[secret_id])
