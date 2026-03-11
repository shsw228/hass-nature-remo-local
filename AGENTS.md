# Repository Guidelines

## Project Structure & Module Organization
This repository is currently in a bootstrap state with no tracked source files yet. Keep the root clean and add code using a predictable layout as the project grows:

- `src/` for application or integration code
- `tests/` for automated tests that mirror `src/`
- `docs/` for specifications and operational notes
- `assets/` for static files such as icons, sample payloads, or screenshots

Example: place a runtime module at `src/nature_remo_local/...` and its tests under `tests/...`.

## Build, Test, and Development Commands
No project-specific build tooling is committed yet. When adding tooling, expose a small, stable command set and document it here.

- `git status --short --branch` checks the working tree before and after changes
- `find . -maxdepth 2 -type f | sort` is useful for quickly reviewing repository contents

If you introduce `Makefile`, `npm`, or language-specific scripts, prefer standard entry points such as `make test` or `npm test`.

## Coding Style & Naming Conventions
Match the style of the language you introduce instead of mixing conventions. Use spaces for indentation unless the formatter for that ecosystem requires otherwise. Prefer descriptive file and module names, and keep directory names lowercase.

- Use `snake_case` for filesystem paths where possible
- Use language-native naming in code, such as `camelCase` or `PascalCase`
- Run the ecosystem formatter before opening a review

## Testing Guidelines
Add tests together with production code. Mirror the source layout in `tests/` so ownership stays obvious. Prefer fast, deterministic unit tests first; add integration tests only where they validate repository-specific behavior.

Name test files after the target module, for example `tests/test_remo_client.*` or `tests/remo_client.test.*`.

## Commit & Pull Request Guidelines
There is no local commit history yet, so use the repository convention from the start: `[type] short description`. Valid types include `feat`, `fix`, `docs`, `refactor`, `test`, and `chore`.

Pull requests should explain purpose, changed paths, verification steps, and any configuration impact. Include screenshots only when UI or rendered output changes.

## Security & Configuration Tips
Do not commit secrets, device tokens, or local network credentials. Keep machine-specific settings in ignored files such as `.env.local`, and document required variables in `docs/` once the project adds runtime configuration.
