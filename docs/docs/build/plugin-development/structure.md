---
title: Plugin Structure
sidebar_label: Plugin Structure
---

# Plugin Structure

## Overview

If you haven't already, start with [What is a Plugin?](/build/plugin-development/overview) to understand the core concept.

This page details how plugins are structured, what files and configurations are required, and how dashAI discovers and loads them.

---

## What is a Plugin Composed of?

A plugin is a Python package with a standardized structure. It consists of 4 main parts:

1. **src**: This folder contains the folder with the **name of the plugin or package**. This is important for proper organization and discovery.

   The folder with the name of the plugin or package must contain all the necessary **Python** and **JSON** files to extend the software.

2. **pyproject.toml**: Configuration file. This determines how the package is created, what metadata it contains, and which classes to register as plugin entry points.

3. **readme.md**: Contains the long description of the package or plugin.

4. **LICENSE**: Determines the type of license the package will have.

---

## Recommended Folder Structure

```text
dashai-my-plugin
│   LICENSE
│   pyproject.toml
│   readme.md
└───src
    └───dashai_my_plugin
        │  example_model.py
        │  ExampleModel.json
```

---

## Required Configuration

For the software to integrate the plugin when installed, it must meet the following requirements:

### 1. Entry Points in pyproject.toml

Your **pyproject.toml** MUST contain an **entrypoint** for each Python class you want to add to dashAI:

```toml
[project.entry-points.'dashai.plugins']
ExampleModel = 'dashai_my_plugin.example_model:ExampleModel'
```

This tells dashAI which classes to register and make available in the UI.

### 2. Keywords Section

Your **pyproject.toml** MUST include a **keywords** section. These tags are displayed when showing the plugin in the dashAI **Plugins** module.

The ONLY valid tags are:

```toml
"DashAI", "Model", "Task", "Dataloaders", "Converter", "Explainer"
```

### Example Keywords Section

```toml
[project]
keywords = [
    "DashAI",
    "Model",
    "Dataloaders"
]
```

---

## Next Steps

- See [Developing a Plugin](/build/plugin-development/develop) for step by step implementation guidance
- Check [Plugin Overview](/build/plugin-development/overview) for a complete working example
- Learn how to [upload your plugin to PyPI](/build/plugin-development/upload)
