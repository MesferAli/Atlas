# Atlas
Enterprise AI Layer

## Security Hardening (Enterprise)
- **AST-based SQL validation**: SQL is parsed via `sqlglot` and restricted to single-statement `SELECT`/`WITH` queries only.
- **DML/DDL blocking**: INSERT/UPDATE/DELETE/DROP/etc. are rejected at the AST level, even if obfuscated.
- **Multi-statement protection**: Query batching is denied to reduce injection risk.
- **Structured security logging**: Validation failures emit structured logs for auditability.

## Testing
- SQL security tests: `python -m pytest tests/test_sql_security.py`
- Unit tests (mocked Oracle client): `python -m pytest tests/unit/test_oracle_connector.py`

## Mocked Testing Environment
- **Client isolation**: `oracledb` is fully mocked to avoid local client dependencies.
- **Async pool simulation**: connection pools and cursors are mocked to emulate real query flows.
- **Enterprise reliability**: tests run consistently in CI/CD without Oracle infrastructure, reducing drift.
