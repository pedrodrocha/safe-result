from resultpy import Result, Ok, Err, map, map_err


class TestResult:
    class TestOk:
        def test_creates_ok_with_value(self):
            ok = Result.ok(42)

            assert ok.status == "ok"
            assert ok.value == 42
            assert isinstance(ok, Ok)

        def test_creates_ok_with_none(self):
            ok = Result.ok(None)

            assert ok.status == "ok"
            assert ok.value is None
            assert isinstance(ok, Ok)

    class TestErr:
        def test_creates_err_with_error(self):
            result = Result.err("An error occurred")
            assert result.status == "err"
            assert result.value == "An error occurred"
            assert isinstance(result, Err)

        def test_creates_err_with_error_object(self):
            error = ValueError("Invalid value")
            result = Result.err(error)
            assert result.status == "err"
            assert result.value == error
            assert isinstance(result, Err)

    class TestMapErr:
        def test_transforms_err_value(self):
            err = Result.err("Not found")
            new_err = err.mapErr(lambda e: f"Error: {e}")

            assert new_err == Err("Error: Not found")
            assert isinstance(new_err, Err)

        def test_transforms_with_error_object(self):
            err = Result.err(ValueError("Invalid input"))
            new_err = err.mapErr(lambda e: RuntimeError(f"Wrapped: {e}"))

            assert isinstance(new_err.value, RuntimeError)
            assert str(new_err.value) == "Wrapped: Invalid input"

        def test_passes_through_ok(self):
            ok = Result.ok(10)
            mapped = ok.mapErr(lambda e: f"Error: {e}")

            assert ok.is_ok() is True
            assert isinstance(mapped, Ok)
            assert mapped.value == 10

    class TestMap:
        def test_transforms_ok_value(self):
            ok = Result.ok(5)
            new_ok = ok.map(lambda x: x * 2)

            print(new_ok)
            print(ok)

            assert new_ok == Ok(10)
            assert isinstance(new_ok, Ok)

        def test_passes_through_err(self):
            result = Result.err("fail")
            mapped = result.map(lambda x: x * 3)

            assert result.is_err() is True
            assert isinstance(mapped, Err)
            assert mapped.value == "fail"

        def test_standalone_function_data_first_pattern(self):
            result = map(Result.ok(3), lambda x: x + 4)
            assert result.value == 7

        def test_standalone_function_data_last_pattern(self):
            add_four = map(lambda x: x + 4)
            result = add_four(Result.ok(6))
            assert result.value == 10

    class TestIsOk:
        def test_returns_true_for_ok(self):
            ok = Result.ok(100)
            assert ok.is_ok() is True

        def test_returns_false_for_err(self):
            err = Result.err("Error")
            assert err.is_ok() is False

    class TestIsErr:
        def test_returns_true_for_err(self):
            err = Result.err("Error")
            assert err.is_err() is True

        def test_returns_false_for_ok(self):
            ok = Result.ok(100)
            assert ok.is_err() is False
