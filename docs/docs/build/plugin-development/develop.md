---
title: Developing a Plugin
sidebar_label: Developing a Plugin
---

# Developing a Plugin

## Prerequisites

Before developing a plugin, ensure you understand:

1. **[What is a Plugin?](/build/plugin-development/overview)**: high level overview of plugin concepts and capabilities
2. **[Plugin Structure](/build/plugin-development/structure)**: how plugins are organized and what dashAI requires

---

## Setup Your Development Environment

To create a plugin, you need access to dashAI's Python classes. There are two approaches:

### Option 1: dashAI as an Installed Library

Install dashAI as a package in your Python virtual environment:

```bash
pip install dashai
```

**Note:** This approach is simpler but limits your ability to test the plugin interactively within dashAI.

### Option 2: Clone the Repository (Recommended)

Clone the dashAI repository for full development and testing capabilities:

```bash
git clone https://github.com/DashAISoftware/DashAI.git
cd DashAI
```

Create a `plugins` folder in the repository root for your plugin development:

```text
DashAI/
├── DashAI/
├── plugins/                  ← Create this folder
├── tests/
├── ...
```

This approach lets you test your plugin in real time as you develop.

---

## Step 1: Identify What You Want to Build

Plugins can extend dashAI with:

- **Machine Learning Models** (`TabularClassificationModel`, `RegressionModel`, `TextGenerationModel`, etc.)
- **Data Loaders** (support for additional dataset formats)
- **Data Converters** (preprocessing, feature engineering, transformations)
- **Explorers** (data visualization and analysis tools)
- **Explainers** (model interpretability tools)
- **Custom Tasks** (entirely new ML problem types)
- **Custom Metrics** (evaluation metrics)

To ensure compatibility, your plugin classes **must extend the appropriate dashAI base class**:

```python
# Example: Creating a tabular classification model
from DashAI.back.models.tabular_classification_model import TabularClassificationModel


class MyCustomModel(TabularClassificationModel):
    def train(self, X, y):
        # Your training logic
        pass
```

---

## Step 2: Implement Your Plugin

1. Create the plugin folder inside the `plugins` directory (if using Option 2 above)
2. Write your Python classes extending appropriate dashAI base classes
3. Create any required JSON configuration files
4. Add the `pyproject.toml` with proper entry points (see [Plugin Structure](/build/plugin-development/structure))
5. Write a README describing your plugin

---

## Recommendations

### Review Existing Plugins

Study working examples to understand best practices:

- **[Real world example](/build/plugin-development/overview):** `dashai-phi-model-package` adds Microsoft Phi models
- **Community plugins:** [pypi.org/search/?q=dashai](https://pypi.org/search/?q=dashai)

### Test Your Plugin During Development

1. Create the Python and JSON files locally (Option 2: clone repository)
2. Place them in the `/plugins` folder
3. Start dashAI and verify your components appear and work correctly
4. Iterate until you're confident in the implementation

### Check for Library Conflicts

After installing new dependencies, verify no package conflicts exist:

```bash
pip check
```

**No conflicts:**

```text
No broken requirements found.
```

**With conflicts:**

```text
fastapi 0.106.0 has requirement starlette<0.28.0,>=0.27.0, but you have starlette 0.20.0.
```

Resolve any conflicts before publishing your plugin.

**It is important that when installing a new library for a plugin or package, it must be included among the dependencies of the plugin or package.**

5. **Use prints in the flow of the added components**

   Including prints in the flow of the component you created can be very useful to verify the proper functioning of the component you have created in the software.
