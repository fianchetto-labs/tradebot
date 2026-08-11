# AWS Credential Custody Policy Templates

These templates define the first hosted AWS boundary for E*Trade credentials:
the TradeBot runtime can read and update one existing Secrets Manager secret,
and KMS key use is constrained to Secrets Manager.

They are policy templates, not a complete infrastructure stack. Replace each
`${...}` placeholder before applying them.

## Runtime Role Policy

Use `etrade-runtime-secret-policy.json` as an identity policy attached to the
service role that runs TradeBot.

The runtime role can:

- Read secret metadata with `secretsmanager:DescribeSecret`.
- Read the current credential document with `secretsmanager:GetSecretValue`.
- Write a new credential version with `secretsmanager:PutSecretValue`.
- Use the credential KMS key only through Secrets Manager in the configured
  region and only for the configured secret ARN.

The runtime role cannot:

- Create or delete secrets.
- List unrelated secrets.
- Change secret resource policies.
- Use the KMS key directly outside Secrets Manager.

## KMS Key Policy

Use `etrade-credential-kms-key-policy.json` as the customer-managed KMS key
policy for the credential key.

The key policy separates three actors:

- The AWS account root principal keeps IAM policy delegation enabled.
- The credential admin role can administer the key but cannot decrypt
  credential data through this template.
- The TradeBot runtime role can encrypt/decrypt only through Secrets Manager
  for the configured region and credential secret ARN.

## Placeholders

| Placeholder | Meaning |
| --- | --- |
| `${AWS_ACCOUNT_ID}` | AWS account id that owns the secret, key, and roles. |
| `${AWS_REGION}` | AWS region for the secret and KMS key. |
| `${TRADEBOT_ETRADE_SECRET_NAME}` | Base Secrets Manager secret name, without the AWS random suffix. |
| `${TRADEBOT_CREDENTIAL_KMS_KEY_ID}` | Customer-managed KMS key id used by the secret. |
| `${TRADEBOT_RUNTIME_ROLE_ARN}` | IAM role assumed by the TradeBot service process. |
| `${TRADEBOT_CREDENTIAL_ADMIN_ROLE_ARN}` | IAM role allowed to administer the credential KMS key. |

Secrets Manager secret ARNs include an AWS-generated suffix, so the runtime
policy uses:

```text
arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:${TRADEBOT_ETRADE_SECRET_NAME}-*
```

If you know the exact secret ARN, replace that wildcarded suffix with the exact
ARN before applying the policy.

## Review Checklist

Before applying these policies:

1. Confirm the secret already exists and uses the intended customer-managed KMS
   key.
2. Confirm the runtime role is dedicated to the TradeBot service environment.
3. Confirm the runtime policy references one secret and one KMS key.
4. Confirm no policy statement grants `secretsmanager:*`, `kms:*`, or resource
   `"*"` for runtime secret or runtime KMS access.
5. Confirm live trading gates remain disabled until the explicit permission
   gate work lands.
