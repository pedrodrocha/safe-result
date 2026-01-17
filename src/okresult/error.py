from abc import ABC
from typing import Optional, TypeVar, Dict, Callable, Union, NoReturn

A = TypeVar("A")
E = TypeVar("E", bound="TaggedError")
F = TypeVar("F", bound="TaggedError")

_NOT_SET = object()


class TaggedError(ABC, Exception):
    """Base class for tagged exceptions with cause tracking.

    Supports both exception and non-exception causes.

    Example:
        >>> class MyError(TaggedError):
        ...     @property
        ...     def tag(self) -> str:
        ...         return "MyError"
        >>> raise MyError("something failed", cause="invalid input")
    """

    __slots__ = ("_message", "_non_exception_cause")

    _message: str
    _non_exception_cause: Optional[object]

    TAG: str

    @property
    def tag(self) -> str:
        return self.TAG

    @property
    def message(self) -> str:
        return self._message

    def __init_subclass__(cls) -> None:
        if not hasattr(cls, "TAG"):
            panic(f"Subclass {cls.__name__} must define TAG class attribute")

    def __init__(self, message: str, cause: Optional[object] = None) -> None:
        """Initialize tagged error with message and optional cause.

        Args:
            message: Error message.
            cause: Optional cause (exception or any object).
        """
        super().__init__(message)
        self._message = message

        if isinstance(cause, BaseException):
            self._non_exception_cause = _NOT_SET
            self.__cause__ = cause  # Python's built-in cause chaining
        else:
            self._non_exception_cause = "None" if cause is None else cause
            self.__cause__ = None

    def __getattribute__(self, name: str) -> Union[BaseException, None, object]:
        return object.__getattribute__(self, name)

    @property
    def cause(self) -> Optional[object]:
        """Get the cause (exception or non-exception).

        Returns:
            The cause if it was set during initialization, None otherwise.
        """
        if self._non_exception_cause is not _NOT_SET:
            cause = self._non_exception_cause
            return None if cause == "None" else cause
        return self.__cause__

    def __str__(self) -> str:
        return self._message

    @staticmethod
    def is_error(value: object) -> bool:
        """Checks if value is an exception.

        Args:
            value: Value to check.

        Returns:
            True if value is an Exception.
        """
        return isinstance(value, Exception)

    @staticmethod
    def is_tagged_error(value: object) -> bool:
        """Checks if value is a TaggedError.

        Args:
            value: Value to check.

        Returns:
            True if value is a TaggedError instance.
        """
        return isinstance(value, Exception) and isinstance(value, TaggedError)

    @staticmethod
    def match[A](
        error: "TaggedError",
        handlers: Dict[type, Callable[..., A]],
    ) -> A:
        """Pattern matches on error type.

        Args:
            error: TaggedError to match.
            handlers: Dict mapping error types to handler functions.

        Returns:
            Result of matched handler.

        Raises:
            ValueError: If no handler found for error type.

        Example:
            >>> class MyError(TaggedError):
            ...     TAG = "MyError"
            >>> handlers = {MyError: lambda e: "handled"}
            >>> TaggedError.match(my_error, handlers)
            'handled'
        """
        handler = handlers.get(type(error))
        if handler is None:
            raise ValueError(f"No handler for error type: {type(error).__name__}")
        return handler(error)

    @staticmethod
    def match_partial[A](
        error: "TaggedError",
        handlers: Dict[type, Callable[..., A]],
        otherwise: Callable[..., A],
    ) -> A:
        """Pattern matches on error type with fallback.

        Args:
            error: TaggedError to match.
            handlers: Dict mapping error types to handler functions.
            otherwise: Fallback handler for unmatched types.

        Returns:
            Result of matched or fallback handler.

        Example:
            >>> class MyError(TaggedError):
            ...     TAG = "MyError"
            >>> handlers = {MyError: lambda e: "handled"}
            >>> TaggedError.match_partial(error, handlers, lambda e: "fallback")
            'handled'
        """
        handler = handlers.get(type(error))
        if handler is None:
            return otherwise(error)
        return handler(error)


class UnhandledException(TaggedError):
    """Exception wrapper for unhandled exceptions.

    Automatically wraps exceptions caught in safe execution.

    Example:
        >>> try:
        ...     raise ValueError("bad value")
        ... except Exception as e:
        ...     err = UnhandledException(e)
    """

    TAG: str = "UnhandledException"

    def __init__(self, cause: object) -> None:
        """Initialize with cause.

        Args:
            cause: The underlying exception or error cause.
        """
        message = f"Unhandled exception: {cause}"
        super().__init__(message, cause)


class Panic(TaggedError):
    """Exception representing unrecoverable errors.

    Used for programming errors and invariant violations.

    Example:
        >>> raise Panic("invariant violated", cause=data)
    """

    TAG: str = "Panic"

    def __init__(self, message: str, cause: Optional[object] = None) -> None:
        """Initialize panic with message and optional cause.

        Args:
            message: Panic message.
            cause: Optional cause (exception or any object).
        """
        super().__init__(message, cause)


def is_panic(value: object) -> bool:
    """Checks if value is a Panic exception.

    Args:
        value: Value to check.

    Returns:
        True if value is a Panic instance.

    Example:
        >>> is_panic(Panic("error"))
        True
    """
    return isinstance(value, Panic)


def panic(message: str, cause: Optional[object] = None) -> NoReturn:
    """Raises a Panic exception.

    Args:
        message: Panic message.
        cause: Optional cause (exception or any object).

    Raises:
        Panic: Always raises.

    Example:
        >>> panic("invariant violated")
        Panic: invariant violated
    """
    raise Panic(message, cause)
