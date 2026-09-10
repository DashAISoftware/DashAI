---
title: Estructura de un Plugin
sidebar_label: Estructura de un Plugin
---

# Estructura de un Plugin

## Visión General

Si aún no lo hiciste, comienza con [¿Qué es un Plugin?](/build/plugin-development/overview) para entender el concepto central.

Esta página detalla cómo se estructuran los plugins, qué archivos y configuraciones son necesarios, y cómo dashAI los descubre y carga.

---

## ¿De Qué se Compone un Plugin?

Un plugin es un paquete Python con una estructura estandarizada. Consta de 4 partes principales:

1. **src**: Esta carpeta contiene la carpeta con el **nombre del plugin o paquete**. Esto es importante para una correcta organización y descubrimiento.

   La carpeta con el nombre del plugin o paquete debe contener todos los archivos **Python** y **JSON** necesarios para extender el software.

2. **pyproject.toml**: Archivo de configuración. Determina cómo se crea el paquete, qué metadatos contiene y qué clases registrar como entry points del plugin.

3. **readme.md**: Contiene la descripción extendida del paquete o plugin.

4. **LICENSE**: Determina el tipo de licencia que tendrá el paquete.

---

## Estructura de Carpetas Recomendada

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

## Configuración Requerida

Para que el software integre el plugin al instalarlo, debe cumplir los siguientes requisitos:

### 1. Entry Points en pyproject.toml

Tu **pyproject.toml** DEBE contener un **entrypoint** por cada clase Python que quieras agregar a dashAI:

```toml
[project.entry-points.'dashai.plugins']
ExampleModel = 'dashai_my_plugin.example_model:ExampleModel'
```

Esto le indica a dashAI qué clases registrar y hacer disponibles en la UI.

### 2. Sección de Keywords

Tu **pyproject.toml** DEBE incluir una sección **keywords**. Estas etiquetas se muestran al presentar el plugin en el módulo **Plugins** de dashAI.

Los únicos tags válidos son:

```toml
"DashAI", "Model", "Task", "Dataloaders", "Converter", "Explainer"
```

### Ejemplo de Sección Keywords

```toml
[project]
keywords = [
    "DashAI",
    "Model",
    "Dataloaders"
]
```

---

## Próximos Pasos

- Ver [Desarrollar un Plugin](/build/plugin-development/develop) para una guía de implementación paso a paso
- Revisar [Visión General de Plugins](/build/plugin-development/overview) para un ejemplo completo y funcional
- Aprender cómo [subir tu plugin a PyPI](/build/plugin-development/upload)
