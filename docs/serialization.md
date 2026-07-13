# Serialization Guidelines

These guidelines define how domain models move between internal Python code and
external boundaries such as HTTP requests, JSON, persisted fixtures, and API
responses.

## Core Rule

Use rich domain objects inside the application. Use primitive JSON-compatible
values at serialization boundaries.

Internal code may use types such as `Amount`, `date`, `Enum`, `Option`, and
`Equity` when they make the domain model clearer. Serialized output should not
contain those objects as dictionary keys or scalar values. It should use strings,
numbers, booleans, nulls, lists, and dictionaries with string keys.

## Dictionary Keys

Python dictionaries can use any hashable object as a key, but JSON object keys
are strings. Pydantic serialization can also recursively convert model objects
into dictionaries, which makes model objects unsafe as serialized dictionary
keys.

Follow these conventions:

- `Amount` keys serialize with `str(amount)`, for example `"25.00 USD"`.
- `date` keys serialize with `date.isoformat()`, for example `"2026-01-16"`.
- `Enum` keys serialize with `enum.value`, for example `"etrade"` or `"PUT"`.
- Pydantic model instances must never appear as keys in `model_dump()` output.
- Validators should parse serialized keys back into rich internal keys when the
  model is validated.

Use the helpers in `fianchetto_tradebot.common_models.serialization` for shared
key conversions instead of reimplementing parsing and formatting in each model.

## Pydantic Dumps

Use the dump mode that matches the boundary:

- Internal inspection or rich Python round trips: `model_dump()`.
- HTTP request bodies, JSON payloads, logs intended as JSON, and persisted JSON:
  `model_dump(mode="json")` or `model_dump_json()`.

Client code that passes payloads to `requests` should use
`model_dump(mode="json")`. This ensures nested dates and enums are converted
before the HTTP library sees the payload.

## Model Serializer Pattern

For a model field with rich dictionary keys:

1. Add a `field_serializer` that emits primitive string keys.
2. Add a matching `field_validator(..., mode="before")` that accepts either the
   rich internal key type or the serialized string form.
3. Keep the field annotation in the rich internal shape if that is what the rest
   of the application uses.

Example shape:

```python
class Example(BaseModel):
    prices: dict[Amount, dict[date, Price]]

    @field_serializer("prices", when_used="always")
    def serialize_prices(self, prices):
        return {
            serialize_amount_key(amount): {
                serialize_date_key(expiry): price
                for expiry, price in expiry_map.items()
            }
            for amount, expiry_map in prices.items()
        }

    @field_validator("prices", mode="before")
    @classmethod
    def deserialize_prices(cls, value):
        if isinstance(value, dict):
            return {
                deserialize_amount_key(amount): {
                    deserialize_date_key(expiry): price
                    for expiry, price in expiry_map.items()
                }
                for amount, expiry_map in value.items()
            }
        return value
```

## Testing Expectations

Tests for serialized models should assert the contract, not only that dumping
does not crash.

For models with custom serialization:

- Assert all serialized dictionary keys are strings.
- Assert important serialized keys have the expected exact value.
- Assert `Model.model_validate(model.model_dump())` rebuilds rich internal keys.
- Assert `Model.model_validate_json(model.model_dump_json())` round-trips.
- For HTTP clients, assert outbound request JSON contains no `date`, `Enum`, or
  `BaseModel` instances.

## Current Examples

The current canonical examples are:

- `Chain`: serializes nested `Amount` and `date` keys.
- `Portfolio`: serializes nested `date`, `Amount`, and `OptionType` keys.
- `ListManagedExecutionsRequest`: serializes `Brokerage` keys.
- `Client.post` and `Client.put`: serialize request bodies in Pydantic JSON mode.
