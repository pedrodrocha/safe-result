from typing import TypeVar, Callable, Awaitable, Literal, Generic, overload
from typing_extensions import TypedDict
import asyncio

from .result import Result, Ok, Err
from .error import UnhandledException, panic

A = TypeVar("A")
E = TypeVar("E")


class RetryConfig(TypedDict, total=False):
    """Configuration for retry behavior in safe.

    Attributes:
        times: Number of retry attempts.
    """

    times: int


class RetryConfigAsync(TypedDict, total=False):
    """Configuration for retry behavior in safe_async.

    Attributes:
        times: Number of retry attempts.
        delay_ms: Delay in milliseconds between retries.
        backoff: Backoff strategy (constant, linear, or exponential).
    """

    times: int
    delay_ms: int
    backoff: Literal["constant", "linear", "exponential"]


class SafeConfig(TypedDict, total=False):
    """Configuration for safe execution.

    Attributes:
        retry: Retry configuration.
    """

    retry: RetryConfig


class SafeConfigAsync(TypedDict, total=False):
    """Configuration for safe async execution.

    Attributes:
        retry: Retry configuration.
    """

    retry: RetryConfigAsync


class SafeOptions(TypedDict, Generic[A, E]):
    """Options for safe execution with custom error handling.

    Attributes:
        try_: Function to execute.
        catch: Function to transform caught exceptions.
    """

    try_: Callable[[], A]
    catch: Callable[[Exception], E]


@overload
def safe(
    thunk: Callable[[], A],
    config: SafeConfig | None = None,
) -> Result[A, UnhandledException]: ...


@overload
def safe(
    thunk: SafeOptions[A, E],
    config: SafeConfig | None = None,
) -> Result[A, E]: ...


def safe(
    thunk: Callable[[], A] | SafeOptions[A, E],
    config: SafeConfig | None = None,
) -> Result[A, E] | Result[A, UnhandledException]:
    """Executes function safely, wrapping result/error in Result.

    Args:
        thunk: Function to execute or options dict with try_ and catch.
        config: Optional retry configuration.

    Returns:
        Result containing value or error.

    Raises:
        Panic: If catch handler throws.

    Example:
        >>> safe(lambda: 1 / 0)
        Err(UnhandledException(...))
        >>> safe({"try_": lambda: parse(x), "catch": lambda e: "error"})
        Err("error")
    """

    def execute() -> Result[A, E] | Result[A, UnhandledException]:
        if callable(thunk):
            try:
                return Ok(thunk())
            except Exception as e:
                return Err(UnhandledException(e))
        else:
            try:
                return Ok(thunk["try_"]())
            except Exception as original_cause:
                # If the user's catch handler throws, it's a defect — Panic
                try:
                    return Err(thunk["catch"](original_cause))
                except Exception as catch_handler_error:
                    panic("Result.safe catch handler threw", catch_handler_error)

    retry_config = (config or {}).get("retry", {})
    times = retry_config.get("times", 0) if retry_config else 0

    result = execute()

    for _ in range(times):
        if result.is_ok():
            break
        result = execute()

    return result


@overload
async def safe_async(
    thunk: Callable[[], Awaitable[A]],
    config: SafeConfigAsync | None = None,
) -> Result[A, UnhandledException]: ...


@overload
async def safe_async(
    thunk: SafeOptions[Awaitable[A], E],
    config: SafeConfigAsync | None = None,
) -> Result[A, E]: ...


async def safe_async(
    thunk: Callable[[], Awaitable[A]] | SafeOptions[Awaitable[A], E],
    config: SafeConfigAsync | None = None,
) -> Result[A, E] | Result[A, UnhandledException]:
    """Executes async function safely, wrapping result/error in Result.

    Supports retry with configurable delay and backoff.

    Args:
        thunk: Async function to execute or options dict with try_ and catch.
        config: Optional retry configuration with delay and backoff.

    Returns:
        Result containing value or error.

    Raises:
        Panic: If catch handler throws.

    Example:
        >>> await safe_async(lambda: fetch(url))
        Ok(...)
        >>> await safe_async(
        ...     lambda: fetch(url),
        ...     {"retry": {"times": 3, "delay_ms": 100, "backoff": "exponential"}}
        ... )
    """

    async def execute() -> Result[A, E] | Result[A, UnhandledException]:
        if callable(thunk):
            try:
                return Ok(await thunk())
            except Exception as e:
                return Err(UnhandledException(e))
        else:
            try:
                return Ok(await thunk["try_"]())
            except Exception as original_cause:
                # If the user's catch handler throws, it's a defect — Panic
                try:
                    return Err(thunk["catch"](original_cause))
                except Exception as catch_handler_error:
                    panic("Result.safe_async catch handler threw", catch_handler_error)

    def get_delay(attempt: int) -> float:
        if not config:
            return 0
        retry_config = config.get("retry")
        if not retry_config:
            return 0
        delay_ms = retry_config.get("delay_ms", 0)
        backoff = retry_config.get("backoff", "constant")
        if backoff == "constant":
            return delay_ms / 1000
        elif backoff == "linear":
            return (delay_ms * (attempt + 1)) / 1000
        else:  # exponential
            return (delay_ms * (2**attempt)) / 1000

    retry_config = (config or {}).get("retry", {})
    times = retry_config.get("times", 0) if retry_config else 0

    result = await execute()

    for attempt in range(times):
        if result.is_ok():
            break
        delay = get_delay(attempt)
        if delay > 0:
            await asyncio.sleep(delay)
        result = await execute()

    return result
