# TradeBot Local Development Setup

This guide is the detailed local setup path for TradeBot contributors. If you
are brand new to the project, start with the friendlier
[New Contributor Quickstart](../docs/new-contributor-quickstart.md), then come
back here when you want more detail.

You do not need brokerage credentials to run the normal development setup or
the safe test suite.

## 1. Get Access

Ask Aleks for GitHub access that lets you clone the repository, push feature
branches, and open pull requests against `fianchetto-labs/tradebot`.

You will also want access to the Fianchetto Labs Linear workspace so you can
claim tickets and link PRs to issues.

Useful setup links:

- [GitHub SSH setup](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
- [Testing your GitHub SSH connection](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/testing-your-ssh-connection)
- [Fianchetto Labs Linear issues](https://linear.app/fianchetto-labs/view/all-issues-1d578a3e4473)

## 2. Clone The Repository

Use SSH:

```bash
git clone git@github.com:fianchetto-labs/tradebot.git
cd tradebot
```

Confirm you are in the Git root:

```bash
git status --short --branch
```

If cloning fails with `Permission denied (publickey)`, confirm that your SSH key
is loaded, added to GitHub, and that you accepted the repository invite.

## 3. Install Python

TradeBot targets Python 3.14.

Check your local version:

```bash
python3.14 --version
```

If that command fails, install Python 3.14 with your normal toolchain. On macOS,
reasonable options include Homebrew, pyenv, or asdf.

## 4. Create A Virtual Environment

```bash
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

The editable install with `.[dev]` is the normal contributor setup. It installs
the package plus development tools such as pytest and Nox.

## 5. Run Tests

Run the safe default suite:

```bash
python -m nox -s unit
```

This should pass without brokerage credentials. Docker-backed and live
brokerage tests are intentionally gated and are not part of the ordinary unit
workflow.

For focused debugging, route pytest through Nox:

```bash
python -m nox -s test -- tests/common/test_chain.py
```

If you intentionally need Docker or live brokerage validation, read the
[Testing guide](../docs/testing.md) first. Those commands require explicit
environment variables so they do not run by accident.

## 6. Optional PyCharm Setup

PyCharm works well for this project.

After opening the repository:

1. Configure the interpreter as `.venv/bin/python`.
2. Mark `src/` as a Sources Root.
3. Mark `tests/` as a Tests Root.

The repo also configures pytest's Python path in `pyproject.toml`, so command
line test runs should not require manually exporting `PYTHONPATH`.

## 7. First Contribution Workflow

1. Pick a Linear ticket.
2. Comment that you are taking it, assign yourself if you have permission, and
   move it to In Progress.
3. Pull the latest `main`.
4. Create a branch with the ticket number:

```bash
git checkout main
git pull --ff-only origin main
git checkout -b githubusername/fia-124-short-slug
```

Use the Linear key in the PR title:

```text
FIA-124: Fix first connection docs
```

Before opening the PR, run the smallest meaningful validation. For code changes,
that usually starts with:

```bash
python -m nox -s unit
```

For docs-only changes, a careful read plus `git diff --check` is usually enough.

## 8. CI

GitHub Actions runs the project checks when you push a branch or open a pull
request. Check the PR page for status and link any surprising failure back to
the Linear ticket or PR discussion.
