# Repository Guidelines

## Project Structure & Module Organization

- Source code lives in `custom_components/ha_fritzprofiles/` (Home Assistant integration).
- Tests are in `tests/` with fixtures in `tests/conftest.py`.
- Translations are in `custom_components/ha_fritzprofiles/translations/`.
- Test fixtures/assets live in `tests/resources/`.

## Build, Test, and Development Commands

- Create a venv and install test deps:
  - `python3 -m venv venv && source venv/bin/activate`
  - `pip install -r requirements_test.txt`
- Run tests (uses pytest config from `setup.cfg`):
  - `pytest --durations=10 --cov-report term-missing --cov=custom_components.ha_fritzprofiles tests`
- Run pre-commit checks (if installed):
  - `prek run --all-files`

## Coding Style & Naming Conventions

- Python 3.13+ (see `setup.cfg`).
- Format with `ruff format` (line length 88) and lint with `ruff check` (config in `pyproject.toml`).
- Follow existing naming: `snake_case` for functions/vars, `PascalCase` for classes.
- Keep changes focused; avoid reformatting unrelated files.

## Testing Guidelines

- Tests use pytest with coverage enforced (coverage fail threshold is 100% in `setup.cfg`).
- Name tests `tests/test_*.py` and test functions `test_*`.
- When changing behavior, add/adjust tests to keep coverage green.

## Home Assistant Testing Conventions

- Use Home Assistant test helpers/fixtures: `hass`, `async_setup_component`, `async_block_till_done`.
- Prefer async tests for HA interactions and assert via the HA state machine (`hass.states.get`).
- Use built-in services (e.g., `select.select_option`) and validate side effects via state/attributes.
- Use `caplog` to assert expected warnings/errors from the integration.

## Pytest Best Practices for This Repo

- Use fixtures for setup; avoid module-level state and setup/teardown functions.
- Use `pytest.mark.parametrize` for variants and error-path coverage.
- Mock at the boundary (FRITZ!Box/network/I/O); use `autospec=True` where possible.
- Assert behavior (state changes, service calls, logged errors), not “no exception”.
- Keep tests deterministic: no real network calls, no sleeps, no wall-clock time.
- Avoid brittle assertions (ordering, full dict equality when only subsets matter).

## Required Mocking

- Always mock FRITZ!Box interactions and network I/O (`requests`, `FritzProfileSwitch` methods).
- Mock executor jobs (`hass.async_add_executor_job`) when verifying side effects.
- Patch `asyncio.sleep` in setup paths to keep tests fast.

## Commit & Pull Request Guidelines

- Recent commits often use short, descriptive prefixes (e.g., `build(deps): …`, `Add …`, `Fix …`).
- Create a branch from `master`, update docs when behavior changes, and ensure ruff + tests pass.
- PRs should include a clear description, steps to test, and link any related issues.

## Security & Configuration Tips

- Do not commit credentials or Home Assistant config files.
- If a change touches integration behavior, note any FRITZ!Box or HA version assumptions.
