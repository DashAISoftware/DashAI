---
title: Uploading a Plugin
sidebar_label: Uploading a Plugin
---

# Uploading a Plugin to PyPI

Once your plugin is developed and tested, you can share it with the dashAI community on [PyPI](https://pypi.org/).

## Prerequisites

Before uploading, ensure you have completed:

1. **[Plugin Structure](/build/plugin-development/structure)**: your plugin has the correct folder and configuration format
2. **[Developing a Plugin](/build/plugin-development/develop)**: your plugin is fully implemented and tested locally

---

## Publishing Your Plugin to PyPI

This guide uses **twine** to upload your package, though other methods are available.

### Step 1: Build Your Package

Install the build tools:

```bash
python -m pip install --upgrade build
```

Build your plugin package:

```bash
python -m build
```

This creates two distribution files in the `dist/` folder:

```text
dist/
├── dashai_my_plugin-0.0.1-py3-none-any.whl
└── dashai_my_plugin-0.0.1.tar.gz
```

### Step 2: Obtain a PyPI API Token

1. Create a [PyPI account](https://pypi.org/account/register/) (if you don't have one)
2. Go to your [API tokens page](https://pypi.org/manage/account/#api-tokens)
3. Click "Add API token"
4. Save the token in a secure location (you'll need it in the next step)

### Step 3: Upload to Test PyPI (Recommended First)

Before uploading to the production PyPI, test your package on [Test PyPI](https://test.pypi.org/):

Install twine:

```bash
python -m pip install --upgrade twine
```

Upload to Test PyPI:

```bash
python -m twine upload --repository testpypi dist/*
```

When prompted, use:

- **Username:** `__token__`
- **Password:** `<your-test-pypi-token>`

Visit `https://test.pypi.org/project/dashai-my-plugin/` to verify your package appears correctly.

### Step 4: Upload to Production PyPI

Once testing is complete, upload to the official PyPI:

```bash
python -m twine upload --repository pypi dist/*
```

When prompted, use:

- **Username:** `__token__`
- **Password:** `<your-pypi-token>`

Your plugin is now live on PyPI! Users can install it with:

```bash
pip install dashai-my-plugin
```

---

## Important Notes

### Naming Convention

Ensure your package uses the `dashai-` prefix (e.g., `dashai-my-plugin`) so dashAI automatically discovers it when installed.

### Package Metadata

Your **pyproject.toml** should include:

- Clear description and keywords
- Entry points for plugin classes
- Homepage and repository links
- License information

### Versioning

Follow [Semantic Versioning](https://semver.org/):

- `0.0.1` for initial releases
- `0.1.0` for minor feature additions
- `1.0.0` for stable releases with API stability

---

## Sharing Your Plugin

After publishing, share your plugin with the community:

1. Add a topic `dashai-plugin` to your GitHub repository
2. Announce it on [GitHub Discussions](https://github.com/DashAISoftware/DashAI/discussions)
3. Consider adding documentation or a tutorial

Happy sharing! 🚀
