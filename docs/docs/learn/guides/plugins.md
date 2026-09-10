---
title: "Module Guide: Plugins"
sidebar_label: Plugins
sidebar_position: 4
---

# Module Guide: Plugins

The plugin system is dashAI's extensibility mechanism. It allows new capabilities (models, tasks, data formats, transformations, explainers, and metrics) to be added to the platform without modifying its core code. Plugins are distributed as standard Python packages on PyPI and installed directly from the dashAI interface.

---

## How the Plugin System Works

dashAI discovers plugins through Python's **entry points** mechanism. When a Python package declares a `dashai.plugins` entry point in its `pyproject.toml`, dashAI's component registry automatically picks it up on startup and makes its components available in the appropriate sections of the interface.

This means:

- A plugin that adds a new model will appear in the Models module's available model list for the task it supports.
- A plugin that adds a new converter will appear in the Notebook's CONVERT panel.
- A plugin that adds a new dataloader will appear in the upload format selection.

No manual registration or configuration is required, since the entry point declaration is sufficient.

---

## What Plugins Can Contribute

A single plugin package can contribute any combination of the following component types:

| Component Type   | Where it appears in dashAI                                |
| ---------------- | --------------------------------------------------------- |
| **Models**       | Models module, available model list for the relevant task |
| **Tasks**        | Models module, task selection landing page                |
| **Data Loaders** | Datasets module, upload format selector                   |
| **Converters**   | Notebook module, CONVERT tab                              |
| **Explainers**   | Models module, EXPLAINABILITY tab                         |
| **Metrics**      | Models module, evaluation metrics for the relevant task   |

---

## Installing Plugins

Navigate to the **PLUGINS** section in the top navigation bar. From there you can:

1. Search for plugins published on PyPI by name or keyword.
2. View plugin descriptions, supported component types, and version information.
3. Install with a single click, and dashAI handles the pip installation and component registration automatically.
4. Restart dashAI if prompted, since some plugins require a restart to fully register their components.

Once installed, new components appear immediately (or after restart) in their respective sections without any further configuration.

---

## Plugin Structure

A dashAI plugin is a standard Python package with a specific structure:

```
plugin_name/
├── LICENSE
├── pyproject.toml
├── README.md
└── src/
    └── plugin_name/
        ├── my_model.py
        └── MyModel.json
```

Each component is implemented as a Python class that extends the appropriate dashAI base class, paired with a JSON schema file that describes its parameters for the interface.

The `pyproject.toml` must declare one entry point per component class:

```toml
[project.entry-points.'dashai.plugins']
MyModel = 'plugin_name.my_model:MyModel'
```

And must include the appropriate keywords so dashAI can categorize the plugin:

```toml
[project]
keywords = ["DashAI", "Package", "Model", "Task"]
```

Valid keywords: `DashAI`, `Package`, `Task`, `Model`, `Dataloader`, `Converter`, `Explainer`

---

## Notable Published Plugins

dashAI's image generation capabilities are themselves distributed as plugins:

| Plugin                                           | What it adds                                     |
| ------------------------------------------------ | ------------------------------------------------ |
| `dashai-stable-diffusion-v1-model-package`       | Stable Diffusion v1 for text-to-image generation |
| `dashai-flux-model-package`                      | Flux model for text-to-image generation          |
| `dashai-stable-diffusion-controlnet-canny-model` | ControlNet with Canny edge conditioning          |

This architecture, where even first party capabilities are plugins, means the core platform stays lean and every feature is opt in based on your hardware and use case.

---

## Developing Your Own Plugins

Building a plugin requires:

1. Creating a Python class that extends the right dashAI base class for your component type (e.g., `TabularClassificationModel` for a tabular classification model).
2. Creating a JSON schema file that describes the component's parameters. This is what dashAI uses to generate the configuration UI automatically.
3. Packaging the code with proper `pyproject.toml` entry points.
4. Testing locally by placing the plugin in a `plugins/` folder inside your dashAI development directory.
5. Publishing to PyPI when ready.

For a complete development guide including code examples, base class references, and a publishing walkthrough, see the [Plugin Development](/build/plugin-development/overview) section.

:::info
The entry point mechanism means any package on PyPI with the correct structure will work. There is no approval process or central registry beyond PyPI itself. You can also install plugins from local paths during development.
:::
