from abc import ABC, abstractmethod
from typing import Optional, TypeVar, Dict, Callable, Mapping

"""
Type variable for a generic result type A
"""
A = TypeVar("A")

"""
Type variable for a generic error type E bounded to TaggedError
"""
E = TypeVar("E", bound="TaggedError")

"""
Type variable for an alternative generic error type F bounded to TaggedError
"""
F = TypeVar("F", bound="TaggedError")


class TaggedError(ABC, Exception):
    __slots__ = ("_message",)

    _message: str

    @property
    @abstractmethod
    def tag(self) -> str: ...

    @property
    def message(self) -> str:
        return self._message

    def __init__(self, message: str, cause: Optional[Exception] = None) -> None:
        super().__init__(message)
        self._message = message
        if cause is not None:
            self.__cause__ = cause  # Python's built-in cause chaining

    def __str__(self) -> str:
        return self._message  # Simple, no "Caused by:" appended

    @staticmethod
    def is_error(value: object) -> bool:
        """
        Type guard for any Exception instance.

        Example:
            if TaggedError.is_error(value):
                print(value.message)
        """
        return isinstance(value, Exception)

    @staticmethod
    def is_tagged_error(value: object) -> bool:
        """
        Type guard for TaggedError instances.
        Example:
            if TaggedError.is_tagged_error(value):
                print(value.tag)
        """
        return isinstance(value, Exception) and isinstance(value, TaggedError)

    @staticmethod
    def match[A](
        error: "TaggedError",
        handlers: Mapping[type["TaggedError"], Callable[..., A]],
    ) -> A:
        """
        Match by concrete error class.

        Handlers can accept the specific error type (e.g., NotFoundError)
        and will receive an instance of that type at runtime.
        """
        error_type = type(error)
        for cls in error_type.__mro__:
            handler = handlers.get(cls)
            if handler is not None:
                # At runtime, error is guaranteed to be an instance of cls
                # We verify this with isinstance for runtime safety
                if not isinstance(error, cls):
                    raise TypeError(
                        f"Expected {cls.__name__}, got {error_type.__name__}"
                    )
                # Callable[..., A] accepts any arguments, so we can pass error directly
                # The runtime guarantee ensures the handler receives the correct type
                return handler(error)
        raise ValueError(f"No handler for error type {error_type.__name__}")

    @staticmethod
    def match_partial[A](
        error: "TaggedError",
        handlers: Dict[str, Callable[..., A]],
        otherwise: Callable[..., A],
    ) -> A:
        """
        Partial pattern match on tagged error union.
        Requires handlers for all _tag variants.
        Returns the result of the handler or the otherwise function if no handler is found.

        Parameters
        ----------
        error : TaggedError
            Error to match.
        handlers : Dict[str, Callable[..., A]]
            Dict mapping _tag to handler function.
            Handlers can accept the specific error type (e.g., NotFoundError)
            and will receive an instance of that type at runtime.
        otherwise : Callable[..., A]
            Function to call if no handler is found.

        Returns
        -------
        A
            Result of matched handler or otherwise function.

        Examples
        --------
        >>> TaggedError.match_partial(error, {
        ...     "NotFoundError": lambda e: f"Missing: {e.id}",
        ...     "ValidationError": lambda e: f"Invalid: {e.field}",
        ... }, lambda e: f"Unknown error: {e.message}")
        """
        tag = error.tag
        handler = handlers.get(tag)
        if handler is None:
            return otherwise(error)
        # Callable[..., A] accepts any arguments, so we can pass error directly
        # The runtime guarantee ensures the handler receives the correct type
        return handler(error)


class UnhandledException(TaggedError):
    @property
    def tag(self) -> str:
        return "UnhandledException"

    def __init__(self, cause: Exception) -> None:
        message = f"Unhandled exception: {cause}"
        super().__init__(message, cause)
