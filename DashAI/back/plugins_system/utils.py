from importlib_metadata import entry_points


def update_plugins(registry_dict_plugins):
    # Retrieve plugins groups (DashAI components)
    task_plugins = entry_points(group="dashai.plugins.task")
    model_plugins = entry_points(group="dashai.plugins.model")
    plugin_groups = {"task": task_plugins, "model": model_plugins}

    for component, plugins in plugin_groups.items():
        if plugins:
            for plugin in plugins:
                # Retrieve plugin class
                plugin_class = plugin.load()
                # Register class into the correspondent registry
                registry_dict_plugins[component].register_component(plugin_class)