from typing import Callable, TypeVar

"""
Generic Input Type A
"""
A = TypeVar("A")

"""
Generic Output Type B
"""
B = TypeVar("B")


def fn(f: Callable[[A], B]) -> Callable[[A], B]:
    """Typed callable factory for lambdas.

    This is the closest semantic equivalent I could getto a typed lambda in Python.
    The type is declared at the factory boundary, not inside the lambda.

    Usage:
        >>> from okresult import fn, map, Ok
        >>>
        >>> # Type inference works automatically
        >>> double = fn(lambda x: x * 2)
        >>> result = Ok(5).map(double)
        >>>
        >>> # For explicit typing, use a regular function with type hints
        >>> def double_func(x: int) -> int:
        ...     return x * 2
        >>> double = fn(double_func)

    Notes:
        - Known limitations:
            - Inline parameter annotations in lambdas (Python limitation)
            - New syntax (Python limitation)
            - Subscriptable syntax like fn[T, U] (requires type suppressions)

    Args:
        f: A callable function from A to B.

    Returns:
        The same function with preserved type information.

    Note:
        Python's typing lives at boundaries, not inside expressions.
        This factory provides the boundary where types are declared.
        For explicit types, define a regular function with annotations.
    """
    return f
