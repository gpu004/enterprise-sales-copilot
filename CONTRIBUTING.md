# Contributing to Enterprise Sales Copilot

Salesforce employees hold `admin` and decide what lands. Everyone else contributes through issues and pull requests.

## Getting started

Setup is in [README.md](README.md). Questions go in a GitHub Issue.

## Issues

Use GitHub Issues for bugs, features, and ideas.

**Bugs.** Search [existing issues](https://github.com/SalesforceAIResearch/enterprise-sales-copilot/issues) first. If it is new, [open one](https://github.com/SalesforceAIResearch/enterprise-sales-copilot/issues/new) with steps to reproduce. Fixes go in a PR that references the issue number and includes a test when you can.

**Features.** Describe the problem in an issue and wait for maintainer feedback before writing a large change.

**Small fixes** (tests, docs, typos) can go straight to a PR. Look for `good first contribution` if you are new.

## Pull requests

1. Search issues before filing a new one.
2. Fork, branch off `main`, commit, push.
3. Open a PR against `main` that references the issue. Keep the diff focused.
4. Sign the [Salesforce CLA](https://cla.salesforce.com/sign-cla) when prompted.

[Sync your fork](https://help.github.com/articles/syncing-a-fork/) before you open the PR.

Expect peer review. Prefer small dependency additions and Apache 2.0 / BSD / MIT / ISC / MPL licenses.

## Code of conduct

[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

## License

By contributing you agree to the project [LICENSE](LICENSE.txt) and the Salesforce CLA.

## Property tests

Run `uv sync --locked` and `uv run pytest -q` from the repository root.
Backend Hypothesis properties cover transcript operation sequences and character
budgets, timezone handling, fenced JSON parsing, LLM response validation, and
parameterized SQLite queries against temporary databases. No API keys are needed.

In `frontend`, run `bun install --frozen-lockfile` and `bun run test`.
[Hegel](https://github.com/hegeldev/hegel-typescript) generates talk-ratio cases;
fast-check checks that splitting speech into segments preserves those ratios.
Use Node 22 or a supported Bun runtime. Both suites run on pull requests.
Generated example caches are ignored; keep regression assertions in the tests.
These tests exercise local logic, not live transcription or model-provider behavior.
