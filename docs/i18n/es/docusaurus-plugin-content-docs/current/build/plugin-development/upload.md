---
title: Subir un Plugin
sidebar_label: Subir un Plugin
---

# Subir un Plugin a PyPI

Una vez que tu plugin está desarrollado y probado, puedes compartirlo con la comunidad de dashAI en [PyPI](https://pypi.org/).

## Requisitos Previos

Antes de subir, asegúrate de haber completado:

1. **[Estructura de un Plugin](/build/plugin-development/structure)**: tu plugin tiene el formato correcto de carpetas y configuración
2. **[Desarrollar un Plugin](/build/plugin-development/develop)**: tu plugin está completamente implementado y probado localmente

---

## Publicar tu Plugin en PyPI

Esta guía usa **twine** para subir tu paquete, aunque hay otros métodos disponibles.

### Paso 1: Construir tu Paquete

Instala las herramientas de build:

```bash
python -m pip install --upgrade build
```

Construye tu paquete plugin:

```bash
python -m build
```

Esto crea dos archivos de distribución en la carpeta `dist/`:

```text
dist/
├── dashai_my_plugin-0.0.1-py3-none-any.whl
└── dashai_my_plugin-0.0.1.tar.gz
```

### Paso 2: Obtener un Token de API de PyPI

1. Crea una [cuenta en PyPI](https://pypi.org/account/register/) (si aún no tienes una)
2. Ve a tu [página de tokens de API](https://pypi.org/manage/account/#api-tokens)
3. Haz clic en "Add API token"
4. Guarda el token en un lugar seguro (lo necesitarás en el siguiente paso)

### Paso 3: Subir a Test PyPI (Recomendado Primero)

Antes de subir al PyPI de producción, prueba tu paquete en [Test PyPI](https://test.pypi.org/):

Instala twine:

```bash
python -m pip install --upgrade twine
```

Sube a Test PyPI:

```bash
python -m twine upload --repository testpypi dist/*
```

Cuando se te solicite, usa:

- **Username:** `__token__`
- **Password:** `<your-test-pypi-token>`

Visita `https://test.pypi.org/project/dashai-my-plugin/` para verificar que tu paquete aparece correctamente.

### Paso 4: Subir a PyPI de Producción

Una vez completadas las pruebas, sube al PyPI oficial:

```bash
python -m twine upload --repository pypi dist/*
```

Cuando se te solicite, usa:

- **Username:** `__token__`
- **Password:** `<your-pypi-token>`

¡Tu plugin ya está disponible en PyPI! Los usuarios pueden instalarlo con:

```bash
pip install dashai-my-plugin
```

---

## Notas Importantes

### Convención de Nombres

Asegúrate de que tu paquete use el prefijo `dashai-` (ej., `dashai-my-plugin`) para que dashAI lo descubra automáticamente al instalarse.

### Metadatos del Paquete

Tu **pyproject.toml** debe incluir:

- Descripción y keywords claras
- Entry points para las clases del plugin
- Links a la página principal y al repositorio
- Información de licencia

### Versionado

Sigue el [Versionado Semántico](https://semver.org/):

- `0.0.1` para lanzamientos iniciales
- `0.1.0` para adiciones de funcionalidades menores
- `1.0.0` para lanzamientos estables con estabilidad de API

---

## Compartir tu Plugin

Después de publicar, comparte tu plugin con la comunidad:

1. Agrega el topic `dashai-plugin` a tu repositorio de GitHub
2. Anúncialo en [GitHub Discussions](https://github.com/DashAISoftware/DashAI/discussions)
3. Considera agregar documentación o un tutorial

¡Feliz publicación! 🚀
