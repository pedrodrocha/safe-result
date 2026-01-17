from okresult import (
    Result,
    Ok,
    Err,
    safe,
    fn,
    map as result_map,
    unwrap,
    TaggedError,
    Panic,
)
import json


class TestQuickStart:
    def test_load_user_example(self) -> None:
        def load_user() -> dict[str, str]:
            return json.loads('{"name": "John", "age": "30"}')

        parsed: Result[dict[str, str], Exception] = safe(load_user)

        if parsed.is_ok():
            user_data = parsed.unwrap()
            assert isinstance(user_data, dict) and "name" in user_data
            assert user_data["name"] == "John"
        else:
            assert False, "Should be ok"

        message = parsed.match(
            {
                "ok": fn[dict[str, str], str](lambda data: f"Got: {data['name']}"),
                "err": fn[Exception, str](
                    lambda e: f"Failed: {getattr(e, 'cause', e)}"
                ),
            }
        )
        assert "Got: John" in message


class TestCreatingResults:
    def test_creates_ok(self) -> None:
        ok = Result.ok(42)
        assert ok.is_ok()

    def test_creates_err(self) -> None:
        err = Result.err(ValueError("failed"))
        assert err.is_err()

    def test_safe_with_throwing_function(self) -> None:
        def risky() -> float:
            raise ValueError("Invalid input")

        result = safe(risky)
        assert result.is_err()

    def test_safe_with_custom_error_handler(self) -> None:
        def risky() -> float:
            raise ValueError("Invalid input")

        result = safe(
            {"try_": risky, "catch": fn[Exception, str](lambda e: "Error: " + str(e))}
        )
        assert result.is_err()


class TestTransformingResults:
    def test_map_and_and_then_chaining(self) -> None:
        result = (
            Ok[int, ValueError](2)
            .map(fn[int, int](lambda x: x * 2))
            .and_then(
                fn[int, Result[int, ValueError]](
                    lambda x: (
                        Ok[int, ValueError](x)
                        if x > 0
                        else Err[int, ValueError](ValueError("negative"))
                    )
                )
            )
        )
        assert result.is_ok()
        assert result.unwrap() == 4

    def test_standalone_map_data_first(self) -> None:
        result = Ok[int, ValueError](5)
        mapped = result_map(result, fn[int, int](lambda x: x + 1))
        assert mapped.is_ok()
        assert mapped.unwrap() == 6

    def test_standalone_map_data_last(self) -> None:
        result = Ok[int, ValueError](5)
        mapper = result_map(fn[int, int](lambda x: x + 1))
        mapped = mapper(result)
        assert mapped.is_ok()
        assert mapped.unwrap() == 6


class TestHandlingErrors:
    class TestMapErr:
        def test_transforms_error_value(self) -> None:
            err_result: Result[int, ValueError] = Result.err(ValueError("invalid"))
            transformed = err_result.map_err(
                fn[ValueError, RuntimeError](lambda e: RuntimeError(str(e)))
            )
            assert transformed.is_err()
            assert isinstance(transformed.unwrap_err(), RuntimeError)

    class TestRecovery:
        def test_recovers_from_specific_errors(self) -> None:
            class NotFoundError(TaggedError):
                TAG = "NotFoundError"
                __slots__ = ("id",)

                def __init__(self, id: str) -> None:
                    super().__init__(f"Not found: {id}")
                    self.id = id

            def fetch_user(id: str) -> Result[dict[str, str], NotFoundError]:
                if id == "valid":
                    return Result.ok({"name": "John", "id": id})
                return Result.err(NotFoundError(id))

            def recover_from_not_found(
                e: NotFoundError,
            ) -> Result[dict[str, str], NotFoundError]:
                return Result.ok({"name": "Default User"})

            result = fetch_user("123").match(
                {
                    "ok": fn[dict[str, str], Result[dict[str, str], NotFoundError]](
                        lambda user: Result.ok(user)
                    ),
                    "err": fn[NotFoundError, Result[dict[str, str], NotFoundError]](
                        lambda e: (
                            recover_from_not_found(e)
                            if e.tag == "NotFoundError"
                            else Result.err(e)
                        )
                    ),
                }
            )
            assert result.is_ok()


class TestExtractingValues:
    def test_unwrap(self) -> None:
        result_ok = Result.ok(42)
        value = unwrap(result_ok)
        assert value == 42
        value = result_ok.unwrap()
        assert value == 42

    def test_unwrap_or(self) -> None:
        result_err = Result.err(ValueError("invalid"))
        value = result_err.unwrap_or(0)
        assert value == 0

    def test_match_for_extraction(self) -> None:
        result_err = Result.err(ValueError("invalid"))
        value = result_err.match(
            {
                "ok": fn[int, int](lambda v: v),
                "err": fn[ValueError, int](lambda e: 0),
            }
        )
        assert value == 0


class TestPanic:
    def test_map_callback_throws_panic(self) -> None:
        try:
            Result.ok(1).map(fn[int, int](lambda x: 1 // 0))
            assert False, "Should have raised Panic"
        except Panic as p:
            assert "map" in p.message.lower()

    def test_catch_handler_throws_panic(self) -> None:
        try:
            safe(
                {
                    "try_": lambda: int("bad"),
                    "catch": fn[Exception, int](lambda e: 1 // 0),  # Bug in handler
                }
            )
            assert False, "Should have raised Panic"
        except Panic as p:
            assert "panic" in str(p).lower() or "safe" in str(p).lower()

    def test_and_then_callback_throws_panic(self) -> None:
        try:
            Result.ok(1).and_then(
                fn[int, Result[int, str]](
                    lambda x: Result.err("error") if False else Result.ok(1 // 0)
                )
            )
            assert False, "Should have raised Panic"
        except Panic:
            pass

    def test_match_handler_throws_panic(self) -> None:
        try:
            Result.ok(1).match(
                {"ok": fn[int, int](lambda x: 1 // 0), "err": fn[str, int](lambda e: 0)}
            )
            assert False, "Should have raised Panic"
        except Panic:
            pass


class TestUnhandledException:
    def test_automatic_unhandled_exception(self) -> None:
        def parse_json(input: str) -> dict[str, str]:
            return json.loads(input)

        # Note: safe without options returns Result with UnhandledException
        # Wrap in lambda to make it a thunk (no-arg callable)
        result: Result[dict[str, str], Exception] = safe(
            lambda: parse_json('{"key": "value"}')
        )
        assert result.is_ok()

    def test_custom_error_handler(self) -> None:
        class ParseError(TaggedError):
            TAG = "ParseError"

            def __init__(self, cause: Exception) -> None:
                super().__init__(f"Parse failed: {str(cause)}")

        def parse_json(input: str) -> dict[str, str]:
            return json.loads(input)

        result: Result[dict[str, str], ParseError] = safe(
            {
                "try_": lambda: parse_json('{"key": "value"}'),
                "catch": fn[Exception, ParseError](lambda e: ParseError(e)),
            }
        )
        assert result.is_ok()


class TestTaggedErrors:
    def test_exhaustive_matching(self) -> None:
        class NotFoundError(TaggedError):
            TAG = "NotFoundError"
            __slots__ = ("id",)

            def __init__(self, id: str) -> None:
                super().__init__(f"Not found: {id}")
                self.id = id

        class ValidationError(TaggedError):
            TAG = "ValidationError"
            __slots__ = ("field",)

            def __init__(self, field: str) -> None:
                super().__init__(f"Invalid: {field}")
                self.field = field

        result_err = Result.err(ValidationError("name"))

        result_exhaustive = TaggedError.match(
            result_err.unwrap_err(),
            {
                ValidationError: fn[
                    ValidationError, Result[dict[str, str], ValidationError]
                ](lambda e: Result.ok({"message": f"Invalid: {e.field}"})),
                NotFoundError: fn[
                    NotFoundError, Result[dict[str, str], ValidationError]
                ](lambda e: Result.ok({"name": "Default User"})),
            },
        )
        assert result_exhaustive.is_ok()

    def test_partial_matching_with_fallback(self) -> None:
        class NotFoundError(TaggedError):
            TAG = "NotFoundError"
            __slots__ = ("id",)

            def __init__(self, id: str) -> None:
                super().__init__(f"Not found: {id}")
                self.id = id

        class ValidationError(TaggedError):
            TAG = "ValidationError"
            __slots__ = ("field",)

            def __init__(self, field: str) -> None:
                super().__init__(f"Invalid: {field}")
                self.field = field

        result_err = Result.err(ValidationError("name"))

        result_partial = TaggedError.match_partial(
            result_err.unwrap_err(),
            {
                ValidationError: fn[
                    ValidationError, Result[dict[str, str], ValidationError]
                ](lambda e: Result.ok({"message": f"Invalid: {e.field}"})),
                NotFoundError: fn[
                    NotFoundError, Result[dict[str, str], ValidationError]
                ](lambda e: Result.ok({"name": "Default User"})),
            },
            otherwise=fn[TaggedError, Result[dict[str, str], ValidationError]](
                lambda e: Result.ok({"message": "Unknown error"})
            ),
        )
        assert result_partial.is_ok()


class TestSerialization:
    def test_serialize_and_hydrate_ok(self) -> None:
        original = Result.ok(42)
        serialized_dict = original.serialize()
        assert serialized_dict == {"status": "ok", "value": 42}

        serialized_json = json.dumps(serialized_dict)
        hydrated = Result.hydrate(json.loads(serialized_json))
        assert hydrated is not None
        assert hydrated.is_ok()

        # Type assertion needed because hydrate returns Result[object, object]
        # We know it's an int from the original, so we can safely unwrap and recreate
        value = hydrated.unwrap() if hydrated.is_ok() else None
        assert value is not None
        assert isinstance(value, int)
        hydrated_int: Result[int, object] = Result.ok(value)
        doubled = hydrated_int.map(fn[int, int](lambda x: x * 2))
        assert doubled.is_ok()
        assert doubled.unwrap() == 84

    def test_serialize_and_hydrate_err(self) -> None:
        err_result = Result.err(ValueError("failed"))
        err_json = json.dumps(err_result.serialize())
        rehydrated = Result.hydrate(json.loads(err_json))
        assert rehydrated is not None
        assert rehydrated.is_err()

    def test_typed_hydration_with_decoders(self) -> None:
        original = Result.ok(42)
        serialized_dict = original.serialize()
        serialized_json = json.dumps(serialized_dict)

        def decode_int(x: object) -> int:
            if isinstance(x, int):
                return x
            raise ValueError("expected int")

        def decode_error(x: object) -> ValueError:
            return ValueError(str(x))

        typed = Result.hydrate_as(
            json.loads(serialized_json),
            ok=decode_int,
            err=decode_error,
        )
        assert typed is not None
        assert typed.is_ok()
        assert typed.unwrap() == 42
