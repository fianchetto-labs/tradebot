# 🧠 TradeBot Developer Onboarding Guide

Welcome to **TradeBot**, the algorithmic trading system by [Fianchetto Labs](https://github.com/Fianchetto-Labs/TradeBot). This guide will help new developers set up their environment and verify their installation to contribute effectively.

---

## 🚀 Getting Started

### 1. Clone the Repository

Use SSH to clone the repository:

```bash
git clone git@github.com:Fianchetto-Labs/TradeBot.git
cd TradeBot
```

> 🔐 **Access Required:**
> If you don't yet have SSH access to the repo, please email the maintainer at:
> 📧 **aleks@fianchettolabs.com**

---

## 🐍 Python Environment

- **Recommended Python version:** `>=3.7`
- Use `virtualenv` (preferred), `conda`, or `pyenv` to manage Python versions and environments.

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install --upgrade pip
```

Install project dependencies (once defined in `requirements.txt` or via `pyproject.toml`):

```bash
pip install -r requirements.txt  # or use poetry/pip-tools as appropriate
```

---

## 🛠 Recommended IDE: PyCharm

We suggest using **PyCharm** for the best experience. Once the project is opened:

1. Mark the following as **Sources Root**:
    - `src/`
2. Mark the following as **Tests Root**:
    - `tests/`

You can do this by right-clicking the folder in PyCharm's file browser → *Mark Directory As* → *Sources Root* or *Tests Root*.


### 🧪 Running Tests in PyCharm

In addition to the command line, you can run tests directly in **PyCharm**:

#### ▶️ Option 1: Run Tests via Right-Click
1. Navigate to the `tests/` directory or a specific test file.
2. Right-click and choose **Run 'pytest in ...'**.
3. PyCharm will automatically use the configured interpreter and show results in the test runner pane.

#### 🐞 Option 2: Debug Tests
1. Right-click a test file or individual test function.
2. Choose **Debug 'pytest for ...'**.
3. This launches the debugger and allows you to set breakpoints, inspect variables, and step through code.

> 💡 Make sure your `src/` and `tests/` folders are properly marked as source roots to ensure correct module resolution.

---

## ✅ Verifying the Setup

To confirm your environment is set up correctly:

1. Add the `src/` and `tests/` directories to your `PYTHONPATH`. In bash:

    ```bash
    export PYTHONPATH=$PYTHONPATH:$(pwd)/src:$(pwd)/tests
    ```

2. Run the tests:

    ```bash
    pytest
    ```

    You should see the test suite run and pass successfully.

---

## 🧪 Continuous Integration (CI)

This project uses **GitHub Actions** to automatically test changes when code is pushed or a pull request is opened.

### 🔄 How it Works

Every time you:

- Push to a branch
- Open a pull request

...GitHub Actions runs the test suite to ensure everything still works.

You can always check the status of the CI pipeline at the top of your pull request or on the repository’s **Actions** tab.
