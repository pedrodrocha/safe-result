from abc import ABC, abstractmethod
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

    @property
    @abstractmethod
    def tag(self) -> str: ...

    @property
    def message(self) -> str:
        return self._message

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
        if name == "__cause__":
            try:
                non_exception_cause = object.__getattribute__(
                    self, "_non_exception_cause"
                )
                if non_exception_cause is not _NOT_SET:
                    return non_exception_cause
            except AttributeError:
                pass
        return object.__getattribute__(self, name)

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
        handlers: Dict[str, Callable[..., A]],
    ) -> A:
        """Pattern matches on error tag.

        Args:
            error: TaggedError to match.
            handlers: Dict mapping tags to handler functions.

        Returns:
            Result of matched handler.

        Raises:
            ValueError: If no handler found for error tag.

        Example:
            >>> handlers = {"MyError": lambda e: "handled"}
            >>> TaggedError.match(my_error, handlers)
            'handled'
        """
        tag = error.tag
        handler = handlers.get(tag)
        if handler is None:
            raise ValueError(f"No handler for error tag: {tag}")
        return handler(error)

    @staticmethod
    def match_partial[A](
        error: "TaggedError",
        handlers: Dict[str, Callable[..., A]],
        otherwise: Callable[..., A],
    ) -> A:
        """Pattern matches on error tag with fallback.

        Args:
            error: TaggedError to match.
            handlers: Dict mapping tags to handler functions.
            otherwise: Fallback handler for unmatched tags.

        Returns:
            Result of matched or fallback handler.

        Example:
            >>> handlers = {"MyError": lambda e: "handled"}
            >>> TaggedError.match_partial(error, handlers, lambda e: "fallback")
        """
        tag = error.tag
        handler = handlers.get(tag)
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

    @property
    def tag(self) -> str:
        return "UnhandledException"

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

    @property
    def tag(self) -> str:
        return "Panic"

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
