# Test

Run all tests (unit + integration).

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

## Unit Tests Only

```bash
pytest tests/unit -v
```

## Integration Tests Only

```bash
pytest tests/integration -v
```
