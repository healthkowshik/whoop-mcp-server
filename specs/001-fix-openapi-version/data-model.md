# Data Model: Fix WHOOP OpenAPI Version Field

## Entities

### OpenAPI Document (JSON)

The root object of the upstream WHOOP API specification.

| Field       | Type   | Required | Notes                          |
|-------------|--------|----------|--------------------------------|
| openapi     | string | yes      | OpenAPI version, e.g. "3.0.1"  |
| info        | object | yes      | See Info Object below           |
| servers     | array  | no       | Server URL definitions          |
| tags        | array  | no       | Endpoint groupings              |
| paths       | object | yes      | Endpoint definitions            |
| components  | object | no       | Reusable schemas                |

### Info Object

The metadata object within the OpenAPI document. This is
the object the CLI command patches.

| Field       | Type   | Required | Notes                          |
|-------------|--------|----------|--------------------------------|
| title       | string | yes      | Currently "WHOOP API"           |
| version     | string | yes      | **Missing upstream**; patched to "2.0.0" when absent |
| description | string | no       | May or may not be present       |

### Patch Rules

- If `info.version` is absent → set to `"2.0.0"`
- If `info.version` is present → preserve as-is
- All other fields in the document → preserve as-is
- Field ordering within `info` → not significant (JSON)
