from __future__ import annotations

__version__ = "0.3.0"

from .result import (
    Err,
    Ok,
    Result,
    Matcher,
    map,
    map_err,
    tap,
    tap_async,
    unwrap,
    and_then,
    and_then_async,
    match,
    Do,
    DoAsync,
)

from .safe import (
    safe,
    safe_async,
    SafeConfig,
    SafeConfigAsync,
    SafeOptions,
    RetryConfig,
    RetryConfigAsync,
)

from .error import TaggedError, UnhandledException, is_panic, panic, Panic

from .fn import fn


__all__ = [
    # Result types
    "Err",
    "Ok",
    "Result",
    "Matcher",
    "Do",
    "DoAsync",
    # Result functions
    "map",
    "map_err",
    "tap",
    "tap_async",
    "unwrap",
    "and_then",
    "and_then_async",
    "Do",
    "match",
    # Safe functions
    "safe",
    "safe_async",
    "UnhandledException",
    "SafeConfig",
    "SafeConfigAsync",
    "SafeOptions",
    "RetryConfig",
    "RetryConfigAsync",
    # Error types
    "TaggedError",
    "UnhandledException",
    "is_panic",
    "panic",
    "Panic",
    # Function types
    "fn",
]
