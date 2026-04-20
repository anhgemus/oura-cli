# Contributing

Thanks for your interest!

## Quick start (uv)

[Install uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```bash
git clone https://github.com/anhdinh/oura-cli && cd oura-cli
uv sync                         # create .venv + install project and dev deps
uv run pytest                   # run tests
uv run ruff check src tests     # lint
uv run oura --version           # run the CLI
```

Prefer raw pip? `pip install -e '.[dev]'` still works — dev deps are mirrored under `[project.optional-dependencies]` on the PyPI release. Locally we use the modern `[dependency-groups]` table that uv reads.

## Guidelines

- **No new runtime deps.** The appeal of this tool is being a stdlib-only wrapper. Dev deps (pytest, ruff, build) are fine.
- **Keep the CLI surface stable.** Additive changes only — renaming a subcommand needs a deprecation alias for at least one minor version.
- **Write tests.** Any new endpoint wrapper, formatter, or summary field should have a unit test in `tests/`.
- **Document quirks.** The Oura API has many sharp edges (date lag, value vs score fields, endpoint 404s). When you find one, document it in the README "Gotchas" section.

## Adding a new endpoint

1. Add the name to `KNOWN_ENDPOINTS` in `src/oura_cli/client.py`.
2. Wire up a typed subcommand in `src/oura_cli/cli.py` via `add_dated(...)` (or a custom handler for non-dated endpoints).
3. Add a row to the README command table.
4. Add a test in `tests/` mocking the response.

## Release

```bash
# bump src/oura_cli/__version__.py, update CHANGELOG.md
git commit -am "Release vX.Y.Z"
git tag vX.Y.Z && git push --tags
# Create a GitHub release from the tag → publish.yml ships to PyPI
```

Or locally:

```bash
uv build
uv publish
```

## Reporting issues

Please include:
- `oura --version`
- The command you ran
- The output (with `-v` if an API call was involved)
- Your Python and uv versions
- Whether you can reproduce against the Oura API directly with `curl`

## Security

Don't open a public issue for credential-leak or token-related bugs — email the maintainer instead.
