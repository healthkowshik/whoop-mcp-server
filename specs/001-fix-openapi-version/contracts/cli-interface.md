# CLI Interface Contract: whoop-fetch-openapi

## Invocation

```
uv run whoop-fetch-openapi [--output PATH]
```

## Arguments

| Argument   | Type   | Default         | Description                      |
|------------|--------|-----------------|----------------------------------|
| --output   | string | `openapi.json`  | Path to write the corrected spec |
| --help     | flag   | N/A             | Show usage and exit              |

## Behavior

1. Fetch JSON from
   `https://api.prod.whoop.com/developer/doc/openapi.json`
2. Parse as JSON
3. If `info.version` is missing, set it to `"2.0.0"`
4. If `info.version` exists, leave it unchanged
5. Write the full document to `--output` path
6. Exit with code 0

## Exit Codes

| Code | Meaning                                    |
|------|--------------------------------------------|
| 0    | Success — corrected spec written to file   |
| 1    | Fetch error — upstream URL unreachable or non-200 |
| 2    | Parse error — response is not valid JSON   |

## Output

- **stdout**: Path to the written file on success
- **stderr**: Error messages on failure
- **File**: Complete OpenAPI 3.0.x JSON document at `--output`
