# Contributing

Thanks for your interest!

## Quick start

```bash
git clone https://github.com/anhdinh/oura-cli
cd oura-cli
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
pytest
ruff check src tests
```

## Guidelines

- **No new runtime deps.** The appeal of this tool is being a single-file-ish stdlib wrapper. Dev dependencies (pytest, ruff) are fine.
- **Keep the CLI surface stable.** Additive changes only — renaming a subcommand needs a deprecation alias.
- **Write tests.** Any new endpoint wrapper, formatter, or summary field should have a unit test in `tests/`.
- **Document quirks.** The Oura API has many sharp edges (date lag, value vs score fields, endpoint 404s). When you find one, document it in the README "Gotchas" section.

## Adding a new endpoint

1. Add the name to `KNOWN_ENDPOINTS` in `src/oura_cli/client.py`.
2. Wire up a typed subcommand in `src/oura_cli/cli.py` via `add_dated(...)` (or a custom handler for non-dated endpoints).
3. Add a row to the README command table.
4. Add a test in `tests/` mocking the response.

## Reporting issues

Please include:
- `oura --version`
- The command you ran
- The output (with `-v` if an API call was involved)
- Your Python version
- Whether you can reproduce against the Oura API directly with `curl`

## Security

Don't open a public issue for credential-leak or token-related bugs — email the maintainer instead.
