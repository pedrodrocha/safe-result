from typing import Callable, Any
from okresult import fn, map, map_err, Result


class TestFn:
    class TestBasicFunctionality:
        def test_returns_same_function(self) -> None:
            def original(x: int) -> int:
                return x * 2
            wrapped = fn(original)
            
            assert wrapped is original
            assert wrapped(5) == 10

        def test_preserves_function_behavior(self) -> None:
            add_one: Callable[[int], int] = fn(lambda x: x + 1)

            assert add_one(5) == 6
            assert add_one(10) == 11

    class TestTypeInference:
        def test_infers_types_from_lambda(self) -> None:
            double: Callable[[int], int] = fn(lambda x: x * 2)

            # Should work with int
            assert double(5) == 10
            assert double(7) == 14

        def test_works_with_string_transformations(self) -> None:
            upper: Callable[[str], str] = fn(lambda s: s.upper())

            assert upper("hello") == "HELLO"
            assert upper("world") == "WORLD"

        def test_works_with_type_conversions(self) -> None:
            to_string: Callable[[object], str] = fn(lambda x: str(x))

            assert to_string(42) == "42"
            assert to_string(True) == "True"

    class TestExplicitTyping:
        def test_works_with_explicitly_typed_functions(self) -> None:
            def double_func(x: int) -> int:
                return x * 2

            typed_double = fn(double_func)

            assert typed_double(5) == 10
            assert typed_double(7) == 14

        def test_works_with_string_typed_functions(self) -> None:
            def format_error(e: str) -> str:
                return f"Error: {e}"

            formatter = fn(format_error)

            assert formatter("not found") == "Error: not found"
            assert formatter("invalid") == "Error: invalid"

    class TestWithResultMap:
        def test_works_with_result_map(self) -> None:
            double: Callable[[int], int] = fn(lambda x: x * 2)
            result: Result[int, Any] = Result.ok(5).map(double)

            assert result.is_ok()
            assert result.unwrap() == 10

        def test_works_with_result_map_chaining(self) -> None:
            double: Callable[[int], int] = fn(lambda x: x * 2)
            add_one: Callable[[int], int] = fn(lambda x: x + 1)

            result: Result[int, Any] = Result.ok(5).map(double).map(add_one)

            assert result.is_ok()
            assert result.unwrap() == 11  # (5 * 2) + 1

        def test_passes_through_err_with_map(self) -> None:
            double: Callable[[int], int] = fn(lambda x: x * 2)
            err_result: Result[Any, str] = Result.err("error")
            mapped: Result[Any, str] = err_result.map(double)

            assert mapped.is_err()
            assert mapped.unwrap_err() == "error"

    class TestWithResultMapErr:
        def test_works_with_result_map_err(self) -> None:
            format_error: Callable[[str], str] = fn(lambda e: f"Error: {e}")
            result: Result[Any, str] = Result.err("not found").map_err(format_error)

            assert result.is_err()
            assert result.unwrap_err() == "Error: not found"

        def test_works_with_error_object_transformation(self) -> None:
            def wrap_error(e: ValueError) -> RuntimeError:
                return RuntimeError(f"Wrapped: {e}")

            wrapper: Callable[[ValueError], RuntimeError] = fn(wrap_error)
            err: Result[Any, ValueError] = Result.err(ValueError("Invalid input"))
            mapped: Result[Any, RuntimeError] = err.map_err(wrapper)

            assert mapped.is_err()
            error_value = mapped.unwrap_err()
            assert isinstance(error_value, RuntimeError)
            assert "Wrapped: Invalid input" in str(error_value)

        def test_passes_through_ok_with_map_err(self) -> None:
            format_error: Callable[[str], str] = fn(lambda e: f"Error: {e}")
            ok_result: Result[int, Any] = Result.ok(42)
            mapped: Result[int, str] = ok_result.map_err(format_error)

            assert mapped.is_ok()
            assert mapped.unwrap() == 42

    class TestWithStandaloneMap:
        def test_works_with_standalone_map(self) -> None:
            double: Callable[[int], int] = fn(lambda x: x * 2)
            result = map(Result.ok(5), double)

            assert result.is_ok()
            assert result.unwrap() == 10

        def test_works_with_standalone_map_err(self) -> None:
            format_error: Callable[[str], str] = fn(lambda e: f"Error: {e}")
            result: Result[Any, str] = map_err(Result.err("failed"), format_error)

            assert result.is_err()
            assert result.unwrap_err() == "Error: failed"

    class TestComplexScenarios:
        def test_works_with_nested_structures(self) -> None:
            get_name: Callable[[dict[str, Any]], Any] = fn(lambda user: user["name"])

            user: dict[str, Any] = {"name": "Alice", "age": 30}
            assert get_name(user) == "Alice"

        def test_works_with_multiple_parameters_via_closure(self) -> None:
            multiplier = 3
            multiply: Callable[[int], int] = fn(lambda x: x * multiplier)

            assert multiply(5) == 15
            assert multiply(7) == 21

        def test_works_in_functional_pipeline(self) -> None:
            double: Callable[[int], int] = fn(lambda x: x * 2)
            to_string: Callable[[int], str] = fn(lambda x: str(x))
            add_prefix: Callable[[str], str] = fn(lambda s: f"Result: {s}")

            result: Result[str, Any] = (
                Result.ok(5).map(double).map(to_string).map(add_prefix)
            )

            assert result.is_ok()
            assert result.unwrap() == "Result: 10"

    class TestEdgeCases:
        def test_works_with_none(self) -> None:
            identity: Callable[[object], object] = fn(lambda x: x)
            result = identity(None)

            assert result is None

        def test_works_with_empty_string(self) -> None:
            upper: Callable[[str], str] = fn(lambda s: s.upper())

            assert upper("") == ""

        def test_works_with_zero(self) -> None:
            double: Callable[[int], int] = fn(lambda x: x * 2)

            assert double(0) == 0

        def test_works_with_boolean(self) -> None:
            negate: Callable[[bool], bool] = fn(lambda x: not x)

            assert negate(True) is False
            assert negate(False) is True
