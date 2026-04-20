# Changelog

All notable changes to this project will be documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/) and this project adheres to
[Semantic Versioning](https://semver.org/).

## [0.1.0] — Unreleased

Initial public release.

### Added
- `OuraClient` — stdlib-only v2 REST client with automatic `next_token` pagination.
- CLI `oura` with typed subcommands for every documented v2 endpoint plus low-level `get`.
- `oura summary` — joins readiness / sleep / activity / stress / spo2 into a single daily digest, with sync-lag fallback.
- `oura export` — bulk dumps every endpoint to JSON files.
- JSON, CSV, and pretty output formatters.
- Auth via `~/.oura_pat`, `OURA_PAT`, `OURA_PAT_FILE`, or `--token`.
