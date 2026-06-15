# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`vire-gap` (distribution name; imports as `vire_gap`) is a Python library of utilities for
the Gemini Enterprise Agent Platform (formerly Vertex AI). Its first module,
`vire_gap.args`, derives an `argparse.ArgumentParser` from a function's type hints — like
`argh`/`fire` (vendored under `ext/` for reference), but tuned for the platform: every
parameter maps to a `--flag` with underscores preserved (`--learning_rate`), and custom
parameter types are built from their string value via argparse's `type=` mechanism.
Early stage. Treat `tests/test_args.py` as the spec.

Python >=3.12, `src/`-based layout (`pythonpath = ["src", "tests"]`), managed with `uv`.

## Commands

- `make test` — run the test suite (`uv run pytest tests/`)
- `uv run pytest tests/test_args.py::test_bool_optional_action` — run a single test
- `make lint` — `uv run ruff check` + `ruff format --check` on `src/ tests/`
- `make fmt` — `uv run ruff format` + `ruff check --fix` on `src/ tests/`

## Architecture

- `src/vire_gap/args.py` — the argparse module. `parser(func)` walks `inspect.signature`
  + `get_type_hints` and calls `add_argument` per parameter; `run(func, argv)` parses and
  dispatches; `arg(type_init=...)` is a decorator stashing per-type string converters on
  the function (`__vire_gap_type_init__`); `to_argv(instance)` is the inverse (dataclass/mapping
  → argv). `_BooleanOptionalAction` replaces `argparse.BooleanOptionalAction` so the
  negated form is `--no_flag` (underscore) instead of `--no-flag`.
- `src/vire_gap/__init__.py` — exposes submodules (`vire_gap.args`); other platform utilities
  go in sibling modules.

Key invariant: CLI flags preserve the parameter name verbatim (`--learning_rate`), unlike
argh which rewrites underscores to hyphens.

## Style Rules (apply to all output: code, comments, docs, commit messages)

- Be succinct. Say it once, say it short.
- No redundant comments. If the code is clear, don't comment it.
- No filler text, no restating the obvious, no "this function does X" before a function named X.
- When asked to "eliminate repetition" or "remove redundant comments", take it literally.
- No fluff, not fuzzy
- Don't remove FIXME/TODO comments unless the user explicitly asks. They track planned work.

## Conventions and Consistency

- Follow existing patterns in the codebase. When in doubt, match what's already there.
- Global project structure matters. Local style within a function or module is flexible.
- If a convention exists (naming, structure, patterns), follow it. Don't introduce alternatives.

## Before writing code

- Before editing any file, read it first. Before modifying a function, code/file search for all callers. Research before you edit.
- Check if a rough design or architecture decision is needed first. Ask if unclear.
- Design around data structures. Get the data model right before implementing logic around it.
- Develop the critical path first — the hard, fundamental part stripped to essentials.
- Don't introduce abstractions preemptively. Duplication is cheaper than the wrong abstraction. Let patterns emerge.
- Think about module and package structure before creating new packages.
- Don't create fine-grained modules with one class each ("categoritis"). Organise by feature, not by category.
- Don't introduce DTOs if not needed. Map directly to domain models when possible.

## Writing code

- One level of abstraction per function. Don't mix high-level orchestration with low-level details.
- Functions should fit on a screen (~80–100 lines max).
- Group code by functional cohesion (things that contribute to the same task), not by class-per-responsibility.
- Favour composition over inheritance.
- Keep dependencies minimal. Don't add libraries for trivial tasks.
- No tactical DDD patterns or hexagonal architecture unless explicitly requested.
- If you don't know a library, read its docs or source on GitHub. Don't guess the API.
- A function belongs in utils only if it's stateless, domain-agnostic, and wouldn't change if the
  business rules changed tomorrow. `chunk_iterable()` qualifies; `calculate_discount()` doesn't,
  even if it looks generic.

## Python specifics

- Naming: `snake_case` modules/functions/variables, `PascalCase` classes, `UPPER_SNAKE_CASE` constants.
  Functions get descriptive verb phrases. `df` is fine in a 5-line scope; name it properly if it travels.
- No bare `except:` — always catch specific exceptions. Keep `try` blocks minimal so unrelated errors
  aren't swallowed.
- Prefer built-in exceptions (`ValueError`, `TypeError`, `KeyError`) before defining custom ones.
- No `assert` for production logic (stripped under `-O`). Fine in tests.
- Validate data at system boundaries (ingestion, external API results), not throughout.
- Docstrings (Google style) on public API functions. Internal helpers only if non-obvious.
- Put (http)-clients into separate classes so I can supply base_path, etc. at construction time

## Types

- Type checker is `basedpyright`.
- Type-hint function signatures; skip obvious local variables.
- Be relaxed about types: add them when straightforward, don't contort code to satisfy the checker.

## Testing

- Write integration and e2e tests early. They catch what AI misses — AI reasons locally, tests verify globally.
- One test per desired external behavior, plus one test per bug.
- Tests target the API of a cohesive unit — not individual classes or internal methods.
- Use tests to find edge cases.
- Don't write tests before the implementation exists (no TDD).
- When fixing bugs: reproduce with a test first, then fix.

## APIs and Interfaces

- Treat APIs as permanent. Don't change signatures without explicit approval.
- Be strict in what you accept and what you return. Don't silently tolerate malformed input.
- Minimize observable behavior surface — anything observable will be depended on.

## Finishing a task

- Tests must pass before marking work done. Run `make lint` and fix what it reports.

## Safety

- Never commit secrets, credentials, or API keys. All secrets come from environment variables.
- Do not read or search files under these directories unless I explicitly ask: node_modules, build, .git, dist, __pycache__, .venv
- If a task is ambiguous, ask one clarifying question rather than guessing.
