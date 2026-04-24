# day2-practice-python

Practice repo for the Claude Code 3-Day Training — Day 2 exercises (2A–2D), Python edition.

## Purpose

Small Python codebase with intentional issues used to practice reading, writing tests, refactoring, and git integration with Claude Code.

## Tech Stack

- Runtime: Python 3.9+
- Test framework: pytest
- Auth: PyJWT (HS256)
- Validation: built-in utilities

## Commands

- `pip install -r requirements.txt` — install dependencies
- `pytest` — run all tests
- `pytest --cov=src --cov-report=html` — run pytest with coverage report

## Conventions

- All new code requires tests before commit
- Branch naming: `feature/*`, `bugfix/*`, `refactor/*`
- Use async/await (but start with synchronous code in 2A–2C)

## Key Files

- `src/auth.py` — JWT auth module (register / login / verify / middleware decorator). Intentionally imperfect.
- `src/validators.py` — five small input validators with hidden bugs.
- `src/legacy_user_data.py` — callback-style DB fetch with SQL-injection and N+1 issues (reserved for Day 3).
- `tests/test_auth.py` — characterization tests pinning current behavior.
- `tests/test_validators.py` — comprehensive test suite covering happy path, edge cases, and bugs.
- `.env.example` — documents the required environment variable.

## Environment

Create a `.env` file in the root (copy from `.env.example`) before running tests.
