# New Contributor Quickstart

Welcome! TradeBot has a lot of surface area, but you do not need to understand
all of it to make a useful first contribution. The goal for day one is simple:
get access, clone the repo, run the safe tests, and pick a small ticket.

## Access Checklist

Ask Aleks for:

- GitHub access that lets you clone `fianchetto-labs/tradebot`, push feature
  branches, and open pull requests.
- A Linear workspace invite for Fianchetto Labs.
- Any project context for the ticket you want to start.

You do not need brokerage credentials for ordinary development, documentation,
unit tests, or simulator-backed work. Live or sandbox brokerage credentials are
only needed for explicitly credentialed E*Trade validation.

## GitHub Setup

1. Create or use your GitHub account.
2. Add an SSH key to GitHub:
   [GitHub SSH setup](https://docs.github.com/en/authentication/connecting-to-github-with-ssh).
3. Accept the repository invite.
4. Confirm SSH works:

```bash
ssh -T git@github.com
```

GitHub should recognize your account. If it says `Permission denied
(publickey)`, the SSH key is either missing from GitHub, not loaded into your
agent, or the repository invite has not been accepted yet.

Useful official docs:

- [Adding a new SSH key to your GitHub account](https://docs.github.com/articles/adding-a-new-ssh-key-to-your-github-account)
- [Testing your SSH connection](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/testing-your-ssh-connection)
- [Managing repository access](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/managing-teams-and-people-with-access-to-your-repository)

## Linear Setup

Accept the Linear invite from your email, then open the Fianchetto Labs
workspace:

- [Fianchetto Labs Linear issues](https://linear.app/fianchetto-labs/view/all-issues-1d578a3e4473)

Useful official docs:

- [Linear invite members](https://linear.app/docs/invite-members)
- [Linear members and roles](https://linear.app/docs/members-roles)

## Clone The Repo

```bash
git clone git@github.com:fianchetto-labs/tradebot.git
cd tradebot
```

If SSH is not ready yet, cloning will fail. Fix GitHub access first; it saves
time later when pushing branches.

## Local Python Setup

TradeBot targets Python 3.14.

Check that it is available:

```bash
python3.14 --version
```

If that command fails, install Python 3.14 with your normal toolchain. On macOS,
Homebrew, pyenv, and asdf are all reasonable choices.

```bash
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run the safe test suite:

```bash
python -m nox -s unit
```

This should pass without brokerage credentials. Docker or live brokerage tests
may be skipped or deselected unless you explicitly enable them.

For a focused test while debugging:

```bash
python -m nox -s test -- tests/common/test_chain.py
```

Avoid running Docker, simulator, or live brokerage tests unless the ticket
explicitly asks for them. Those are intentionally gated.

## Good First Tickets

These are useful places to start. Pick one, read the surrounding code/docs, and
ask Aleks for any missing background before going deep. When you choose one,
comment on the ticket, assign yourself if you have permission, and move it to In
Progress.

| Ticket | Why it is a good start |
| --- | --- |
| [FIA-124: Fix `First Call to Verify Connection` section in docs](https://linear.app/fianchetto-labs/issue/FIA-124/fix-first-call-to-verify-connection-section-in-docs) | Small docs fix that teaches the current client shape. |
| [FIA-130: Add file for PyPI packaging and GitHub tagging for TradeBot-Quickstart](https://linear.app/fianchetto-labs/issue/FIA-130/add-file-for-pypi-packaging-and-github-tagging-for-tradebot-quickstart) | Documentation-heavy warmup with low production risk. |
| [FIA-66: Add a ways-of-working file](https://linear.app/fianchetto-labs/issue/FIA-66/add-a-ways-of-working-file-that-explains-the-standards-and-norms-of) | Helps make future collaboration smoother. |
| [FIA-150: Document simulator-backed deployment mode](https://linear.app/fianchetto-labs/issue/FIA-150/document-simulator-backed-deployment-mode) | Good if you want to learn the Docker/simulator direction without touching live brokerage credentials. |
| [FIA-151: Add pytest markers and test layout conventions](https://linear.app/fianchetto-labs/issue/FIA-151/add-pytest-markers-and-test-layout-conventions-for-the-test-pyramid) | Good if you like test infrastructure and clean project conventions. |

## Project Docs To Skim

Start with these:

- [README](../README.md)
- [Testing guide](testing.md)
- [Developer local setup](../dev_get_started_guides/set_up_local_env.MD)

Then read whichever one matches your ticket:

- [Serialization conventions](serialization.md)
- [Service ports and adapter boundaries](service-ports.md)
- [E*Trade simulator contract](etrade-simulator-contract.md)
- [Publishing and tagging](../dev_get_started_guides/publishing_and_tagging.MD)
- [Brokerage setup](../dev_get_started_guides/exchange_setup.MD) only if your
  ticket explicitly needs real or sandbox brokerage credentials.

## Branch And PR Convention

Start from the latest `main`, then create a branch with the Linear ticket
number:

```bash
git checkout main
git pull --ff-only origin main
git checkout -b githubusername/fia-124-short-slug
```

Use the ticket number in the PR title so GitHub and Linear link it:

```text
FIA-124: Fix first connection docs
```

Before opening the PR, run the smallest meaningful validation. For docs-only
changes, that may just be a careful reread. For code changes, run at least:

```bash
python -m nox -s unit
```

## First-Day Goal

The best first milestone is intentionally small:

1. Accept GitHub and Linear invites.
2. Clone the repo.
3. Install the dev environment.
4. Run `python -m nox -s unit`.
5. Pick one starter ticket and open a draft PR.

That is enough. The rest of the system will make more sense after one small
change has gone through the loop.
