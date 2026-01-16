# Change Log

## [v0.2.0] - yyyy-mm-dd
  
### Added

- `fn` helper for typed lambda expressions: `fn[int, int](lambda x: x * 2)`
- `Panic` exception class for signaling defects in user-provided callbacks
- Docstrings for all public APIs in `result.py`, `error.py`, and `safe.py`
 
### Changed

- User callback exceptions are now converted to `Panic` to distinguish defects from expected error handling
- Match handlers are now wrapped with try/panic to catch exceptions and signal defects
- All async transformation functions use proper `Awaitable` type hints for callbacks
- `is_ok()` and `is_err()` are now concrete implementations in the base `Result` class using the `status` property
 
### Fixed
