# resultpy

Lightweight Result type for Python, inspired by [better-result](https://github.com/dmmulroy/better-result).

## Install

```bash
pip install resultpy
```

## Quick Start

```python
from resultpy import Result, safe
from json import loads

# Wrap throwing functions
parsed = safe(lambda: loads('{"name": "John", "age": 30}'))

# Check and use
if parsed.is_ok():
    print(parsed.unwrap())
else:
    print(parsed.unwrap_err())

# Or use pattern matching
message = parsed.match({
    "ok": lambda data: f"Got: {data['name']}",
    "err": lambda e: f"Failed: {e.cause}",
})
```

## Contents

- [Creating Results](#creating-results)
- [Transforming Results](#transforming-results)
- [Handling Errors](#handling-errors)
- [Extracting Values](#extracting-values)
- [Retry Support](#retry-support)
- [Generator Composition](#generator-composition) *(TODO)*
- [Tagged Errors](#tagged-errors) *(TODO)*
- [Serialization](#serialization) *(TODO)*
- [API Reference](#api-reference)

## Creating Results

```python
from resultpy import Result, Ok, Err, safe, safe_async

# Success
ok = Result.ok(42)

# Error
err = Result.err(ValueError("failed"))

# From throwing function
result = safe(lambda: risky_operation())

# From async function
result = await safe_async(async_operation)

# With custom error handling
result = safe({
    "try_": lambda: parse(input),
    "catch": lambda e: ParseError(str(e)),
})
```

## Transforming Results

```python
from resultpy import Ok, Err, map as result_map

result = (
    Ok[int, ValueError](2)
    .map(lambda x: x * 2)  # Ok(4)
    .and_then(
        # Chain Result-returning functions
        lambda x: Ok[int, ValueError](x) if x > 0 else Err[int, ValueError](ValueError("negative"))
    )
)

# Standalone functions (data-first or data-last)
result_map(result, lambda x: x + 1)
result_map(lambda x: x + 1)(result)  # Pipeable
```

## Handling Errors

```python
from resultpy import Result, Err

err_result: Result[int, ValueError] = Err[int, ValueError](ValueError("invalid"))

# Transform errors
err_result.map_err(lambda e: RuntimeError(str(e)))  # Err(RuntimeError(...))

# Fallback values
err_result.unwrap_or(0)  # 0

# Pattern match
err_result.match({
    "ok": lambda x: f"Got {x}",
    "err": lambda e: f"Failed: {e}"
})
```

## Extracting Values

```python
from resultpy import Result, unwrap

result_ok = Result.ok(42)
result_err = Result.err(ValueError("invalid"))

# Unwrap (throws on Err)
value = unwrap(result_ok)
value = result_ok.unwrap()
value = result_ok.unwrap("custom error message")

# With fallback
value = result_err.unwrap_or(0)

# Pattern match
value = result_err.match({
    "ok": lambda v: v,
    "err": lambda e: fallback,
})
```

## Retry Support

```python
from resultpy import safe, safe_async

# Sync retry
result = safe(risky, {"retry": {"times": 3}})

# Async retry with backoff
result = await safe_async(
    fetch_data,
    {
        "retry": {
            "times": 3,
            "delay_ms": 100,
            "backoff": "exponential",  # or "linear" | "constant"
        }
    }
)
```

## Generator Composition

*TODO: Coming soon*

## Tagged Errors

*TODO: Coming soon*

## Serialization

*TODO: Coming soon*

## API Reference

### Result

| Function | Description |
|----------|-------------|
| `Result.ok(value)` | Create success |
| `Result.err(error)` | Create error |
| `safe(fn, config?)` | Wrap throwing function with optional retry |
| `safe_async(fn, config?)` | Wrap async function with optional retry |
| `unwrap(result, message?)` | Extract value or raise |
| `map(result, fn)` | Transform success value (data-first) |
| `map(fn)(result)` | Transform success value (data-last) |

### Instance Methods

| Method | Description |
|--------|-------------|
| `.is_ok()` | Check if Ok |
| `.is_err()` | Check if Err |
| `.map(fn)` | Transform success value |
| `.map_err(fn)` | Transform error value |
| `.and_then(fn)` | Chain Result-returning function |
| `.and_then_async(fn)` | Chain async Result-returning function |
| `.match({"ok": fn, "err": fn})` | Pattern match |
| `.unwrap(message?)` | Extract value or raise |
| `.unwrap_or(fallback)` | Extract value or return fallback |
| `.unwrap_err(message?)` | Extract error or raise |
| `.tap(fn)` | Side effect on success |
| `.tap_async(fn)` | Async side effect on success |

## License

MIT
