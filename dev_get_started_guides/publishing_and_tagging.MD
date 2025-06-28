## 📦 Publishing a New Release to PyPI

This guide outlines how to prepare and upload a new version of the `fianchetto-tradebot` package to [PyPI](https://pypi.org/).

We do **periodic point releases** as we add new functionality and improve the package. Larger milestones may warrant minor version bumps, and we adhere to [semantic versioning](https://semver.org/) as described below.

### 🔢 Versioning Policy

We use three-part version numbers: `MAJOR.MINOR.PATCH` (e.g. `0.1.15`):

- **Major** version: introduces breaking changes
- **Minor** version: used for major milestones or substantial features
- **Patch** (point-release): used for incremental updates and bug fixes

➡️ Compatibility is guaranteed between all minor versions within a major version, starting at **1.0.0**.

⚠️ Versions below `1.0.0` are considered **alpha (pre-production)** and are not guaranteed to maintain backward compatibility.

---

### ✅ 1. Ensure You're on the Latest `main`

```bash
git checkout main
git pull origin main
```

---

### 🌿 2. Create a New Revision Branch

```bash
git checkout -b <yournameandfirstinitial>/rev/rev-<version>
```

**Example:**
```bash
git checkout -b ashulman/rev/rev-0.1.15
```

---

### 🛠️ 3. Update Dependencies

Open `pyproject.toml` and update any outdated dependencies as needed.

---

### 🏷️ 4. Update the Version

Inside `pyproject.toml`, bump the version:

```toml
version = "0.1.15"
```

Ensure the version follows [semantic versioning](https://semver.org/) and is newer than the last published version.

---

### 🧪 5. Run the Test Suite

Run all tests to ensure the package is in a good state:

```bash
pytest
```

---

### 🧹 6. Remove Old Build Artifacts

Carefully delete the old `dist` directory:

```bash
rm -rf ./dist
```

> ⚠️ **Double-check you're in the correct directory before running this command!**

---

### 🏗️ 7. Build the Distribution

Create a new wheel and source distribution:

```bash
python -m build
```

---

### 📄 8. Confirm the Build Output

Ensure the output includes lines like:

```text
Successfully built fianchetto_tradebot-0.1.15.tar.gz and fianchetto_tradebot-0.1.15-py3-none-any.whl
```

---

### 🚀 9. Upload to PyPI Using Twine

Install `twine` if needed:

```bash
pip install twine
```

Upload the built distributions:

```bash
twine upload dist/*
```

---

### 🔐 10. Enter Your PyPI Credentials

When prompted, enter your PyPI username and **access key** (not your password!).

You can create and manage access tokens from your [PyPI account settings](https://pypi.org/manage/account/token/).

---

### 🔎 11. Verify the Release

Visit your package on PyPI:

👉 [https://pypi.org/project/fianchetto-tradebot/](https://pypi.org/project/fianchetto-tradebot/)

Check that the version and files appear correctly.

---

### 🏁 12. Tag the Release on GitHub

Once your `rev` branch has been committed and pushed, go to the GitHub release page:

👉 [Create a new release](https://github.com/fianchetto-labs/tradebot/releases/new)

Use the version tag in the format:

```text
v<major>.<minor>.<patch>
```

All builds below major version 1 are considered **alpha** and should include the suffix `-alpha`:

```text
v0.1.15-alpha
```

Include release notes or a changelog as needed.

---

🎉 **Done!** You've published a new version of `fianchetto-tradebot` to PyPI and GitHub.