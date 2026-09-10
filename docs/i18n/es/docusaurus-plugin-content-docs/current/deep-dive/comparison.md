---
title: Benchmark comparativo
description: Comparación de dashAI con KNIME, Orange y WEKA en licencia, extensibilidad y cobertura de tareas.
sidebar_label: Benchmark comparativo
---

# Benchmark comparativo

Esta sección compara dashAI con KNIME Analytics Platform, Orange Data Mining y WEKA, tres plataformas de machine learning de código abierto y sin código que cumplen los criterios de selección descritos en la sección de Metodología a continuación.

---

## Metodología

El conjunto de plataformas consideradas se restringió a herramientas que satisfacen conjuntamente tres condiciones: distribución de código abierto, operación sin código para el usuario final, y una arquitectura de catálogo que puede ser extendida por terceros. KNIME Analytics Platform, Orange Data Mining y WEKA cumplen estas condiciones junto con dashAI.

La comparación se organiza en torno a tres dimensiones medibles: los términos de licencia, el mecanismo de extensión, y la cobertura de paradigmas de tareas del catálogo nativo. Para las dimensiones de licencia y extensibilidad, cada afirmación a continuación está vinculada directamente a su fuente primaria (texto oficial de la licencia, documentación oficial para desarrolladores, o el archivo fuente correspondiente), ya sea en línea o en la sección de [Fuentes](#fuentes). Para la dimensión de cobertura de tareas, los conteos de catálogo se obtuvieron mediante inspección directa de la propia interfaz de cada plataforma (repositorio de nodos, catálogo de widgets, gestor de paquetes, o catálogo de modelos) en lugar de a partir de un único listado externo, ya que ninguna de las cuatro plataformas publica un conteo canónico desglosado de esta manera; consulte [Fuentes](#fuentes) para más detalle.

---

## Licencia

dashAI se distribuye bajo la **[licencia MIT](https://docs.dash-ai.com/discover/overview/)**, que permite el uso, la modificación y la redistribución —incluso en entornos comerciales o institucionales— sujeto a la conservación del aviso de copyright y licencia original.

[KNIME](https://www.knime.com/downloads/full-license) y [Orange](https://orangedatamining.com/license/) se distribuyen bajo GPLv3; [WEKA](https://waikato.github.io/weka-wiki/faqs/commercial_applications/), bajo GPL. Las tres licencias imponen obligaciones de copyleft sobre los trabajos derivados distribuidos. KNIME además ofrece funcionalidades no incluidas en su distribución de código abierto —programación de tareas, despliegue gobernado, control de acceso basado en roles, y la AI Extension— disponibles únicamente a través de [KNIME Business Hub](https://www.knime.com/knime-business-hub) bajo una licencia comercial.

---

## Extensibilidad

dashAI expone [doce clases base](https://docs.dash-ai.com/api/back.html), organizadas por rol funcional, incluyendo `BaseModel`, `BaseMetric`, `BaseTask` y `BaseExplainer`. Un nuevo componente se implementa creando una subclase de la clase base correspondiente y declarando sus parámetros mediante un esquema de Pydantic; [la plataforma deriva el formulario de configuración que se muestra en la interfaz directamente de este esquema](https://docs.dash-ai.com/deep-dive/architecture/), sin código adicional de frontend. El componente resultante se distribuye vía PyPI y se instala desde la propia interfaz de dashAI.

Los mecanismos de extensión de las otras tres plataformas son los siguientes:

- **Orange** permite [extensiones en Python](https://orange3.readthedocs.io/projects/orange-development/en/latest/tutorial.html), pero cada widget debe acoplarse a Qt/PyQt e [instanciar manualmente los controles de la interfaz](https://orange3.readthedocs.io/projects/orange-development/en/latest/tutorial-settings.html), ya que no existe generación automática de formularios a partir de esquemas.
- **WEKA** sigue una arquitectura de plugins organizada en familias principales de componentes, incluidas clasificadores, agrupadores, asociadores, filtros, métodos de selección de atributos y cargadores de datos. Cada familia expone su propia API de extensión mediante clases base abstractas y/o interfaces (por ejemplo, `AbstractClassifier` para clasificadores y `Filter` para filtros). Los nuevos clasificadores suelen implementarse heredando de `AbstractClassifier` y redefiniendo los métodos `buildClassifier(Instances)` y `distributionForInstance(Instance)`, que operan sobre la abstracción de datos `Instances` de WEKA. La [estructura del repositorio de WEKA](https://github.com/Waikato/weka-3.8/tree/master), la [Javadoc de AbstractClassifier](https://weka.sourceforge.io/doc.dev/weka/classifiers/AbstractClassifier.html) y la [Javadoc de Filter](https://weka.sourceforge.io/doc.dev/weka/filters/Filter.html) documentan estos puntos de extensión.
- **KNIME**, por la vía oficial, requiere un [plugin OSGi/Eclipse con cuatro clases Java](https://docs.knime.com/latest/analytics_platform_new_node_quickstart_guide/) (`NodeFactory`, `NodeModel`, `NodeDialog` y `NodeView`), además de descriptores `plugin.xml` y `MANIFEST.MF`, y una compilación Maven/Tycho. Desde la versión 4.6 existe una [vía experimental en Python (Labs)](https://docs.knime.com/latest/pure_python_node_extensions_guide/) que genera un diálogo a partir de declaraciones de parámetros, pero no reemplaza la vía Java como enfoque oficial y requiere sus propias herramientas de empaquetado (`pixi`, `knime.yml`).

### Arquitectura de la interfaz

dashAI adopta una [arquitectura cliente-servidor](https://docs.dash-ai.com/deep-dive/architecture/): un servidor FastAPI expone el catálogo de componentes, los datasets, los trabajos de entrenamiento y los resultados; un frontend en React consume esa API vía HTTP. Cuando se registra un nuevo componente, el servidor expone su esquema JSON y el frontend renderiza el formulario de configuración sin conocimiento previo del componente. El servidor puede ejecutarse en cualquier máquina y ser accedido desde un navegador, incluso desde otro dispositivo en la misma red local.

[KNIME está construido sobre Eclipse RCP](https://www.knime.com/open-source-story), [Orange sobre PyQt](https://github.com/biolab/orange3), y [WEKA sobre Java Swing](https://weka.sourceforge.io/doc.stable/weka/gui/explorer/Explorer.html). En los tres casos la interfaz y la lógica de negocio se ejecutan en el mismo proceso; agregar un nuevo componente también requiere modificar la capa de presentación.

---

## Cobertura de tareas

El catálogo nativo de dashAI cubre cuatro tareas predictivas: clasificación tabular, regresión y clasificación de texto, cada una con quince modelos, y traducción, con nueve. Además incluye cinco modelos de lenguaje de gran tamaño (LLMs) y once modelos de generación de imágenes. Todos los modelos del catálogo nativo se ejecutan localmente. La optimización de hiperparámetros se soporta mediante dos frameworks integrados, Optuna y HyperOpt.

La interfaz está disponible en español, inglés, chino, alemán y portugués.

---

## Tabla comparativa

| Criterio                          |                                                                                       KNIME                                                                                       |                                                 Orange                                                  |                                               WEKA                                                |                                  **dashAI**                                   |
| --------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :-----------------------------------------------------------------------------------------------------: | :-----------------------------------------------------------------------------------------------: | :---------------------------------------------------------------------------: |
| **Licencia**                      |                                                                                                                                                                                   |                                                                                                         |                                                                                                   |                                                                               |
| Licencia                          |                                                               [GPLv3](https://www.knime.com/downloads/full-license)                                                               |                             [GPLv3](https://orangedatamining.com/license/)                              |             [GPL](https://waikato.github.io/weka-wiki/faqs/commercial_applications/)              |            **[MIT](https://docs.dash-ai.com/discover/overview/)**             |
| Sin muro de pago en producción    |                                                                  [No](https://www.knime.com/knime-business-hub)                                                                   |                               [Sí](https://orangedatamining.com/license/)                               |              [Sí](https://waikato.github.io/weka-wiki/faqs/commercial_applications/)              |             **[Sí](https://docs.dash-ai.com/discover/overview/)**             |
| **Extensibilidad**                |                                                                                                                                                                                   |                                                                                                         |                                                                                                   |                                                                               |
| Lenguaje de extensión             | [Java (oficial)](https://docs.knime.com/latest/analytics_platform_new_node_quickstart_guide/) / [Python (Labs)](https://docs.knime.com/latest/pure_python_node_extensions_guide/) | [Python + Qt/PyQt](https://orange3.readthedocs.io/projects/orange-development/en/latest/tutorial.html)  |      [Java](https://waikato.github.io/weka-blog/posts/2018-10-08-making-a-weka-classifier/)       |        **[Python](https://docs.dash-ai.com/deep-dive/architecture/)**         |
| Abstracciones por rol funcional   |                       [1 (nodo genérico)](https://github.com/knime/knime-core/blob/master/org.knime.core/src/eclipse/org/knime/core/node/NodeFactory.java)                        | [1 (widget genérico)](https://orange3.readthedocs.io/projects/orange-development/en/latest/widget.html) |               [6 jerarquías Java](https://github.com/Waikato/weka-3.8/tree/master)                |         **[12 clases base](https://docs.dash-ai.com/api/back.html)**          |
| Tipo de interfaz                  |                                                          [Escritorio (Eclipse)](https://www.knime.com/open-source-story)                                                          |                         [Escritorio (PyQt)](https://github.com/biolab/orange3)                          | [Escritorio (Java Swing)](https://weka.sourceforge.io/doc.stable/weka/gui/explorer/Explorer.html) | **[Web (React + FastAPI)](https://docs.dash-ai.com/deep-dive/architecture/)** |
| UI autogenerada                   |                                                    [Parcial](https://docs.knime.com/latest/pure_python_node_extensions_guide/)                                                    |    [No](https://orange3.readthedocs.io/projects/orange-development/en/latest/tutorial-settings.html)    |     [Parcial](https://waikato.github.io/weka-blog/posts/2018-10-08-making-a-weka-classifier/)     |          **[Sí](https://docs.dash-ai.com/deep-dive/architecture/)**           |
| Soporte GPU                       |                                                                                      Parcial                                                                                      |                                                 Parcial                                                 |                                              Parcial                                              |                                  **Parcial**                                  |
| Interfaz multilingüe              |                                                                                        No                                                                                         |                                                   No                                                    |                                                No                                                 |                                    **Sí**                                     |
| **Catálogo nativo**               |                                                                                                                                                                                   |                                                                                                         |                                                                                                   |                                                                               |
| Modelos de clasificación tabular  |                                                                                        ~11                                                                                        |                                                   ~12                                                   |                                                ~39                                                |                                      15                                       |
| Modelos de regresión              |                                                                                        ~9                                                                                         |                                                   ~12                                                   |                                                ~32                                                |                                      15                                       |
| Modelos de clasificación de texto |                                                                                      Parcial                                                                                      |                                                 Parcial                                                 |                                              Parcial                                              |                                      15                                       |
| Modelos de traducción             |                                                                                      Parcial                                                                                      |                                                   No                                                    |                                                No                                                 |                                       9                                       |
| LLMs ejecutados localmente        |                                                                                        No                                                                                         |                                                   No                                                    |                                                No                                                 |                                       5                                       |
| Modelos de generación de imágenes |                                                                                      Parcial                                                                                      |                                                   No                                                    |                                                No                                                 |                                      11                                       |
| Frameworks de HPO integrados      |                                                                                         1                                                                                         |                                                    0                                                    |                                                 1                                                 |                                       2                                       |

**Leyenda:** Sí = soporte nativo completo, Parcial = soporte parcial o requiere extensiones adicionales, No = no soportado

---

## Fuentes

**Licencia**

- Licencia de KNIME (GPLv3 + excepción de node-API): https://www.knime.com/downloads/full-license
- Historia de código abierto de KNIME (contexto de licencia, base Eclipse): https://www.knime.com/open-source-story
- KNIME Business Hub (funcionalidades solo comerciales: programación, gobernanza, RBAC, AI Gateway): https://www.knime.com/knime-business-hub
- Licencia de Orange: https://orangedatamining.com/license/
- Repositorio de Orange3 en GitHub (GPLv3+, dependencia de PyQt): https://github.com/biolab/orange3
- FAQ de licenciamiento de WEKA (GPL 2.0 para 3.6, GPL 3.0 para >3.7.5): https://waikato.github.io/weka-wiki/faqs/commercial_applications/
- Licencia de dashAI (MIT): https://docs.dash-ai.com/discover/overview/

**Extensibilidad**

- KNIME: Create a New KNIME Extension (Quickstart Guide, vía Java: NodeFactory/NodeModel/NodeDialog/NodeView, plugin.xml, MANIFEST.MF): https://docs.knime.com/latest/analytics_platform_new_node_quickstart_guide/
- KNIME: Pure Python Node Extensions Guide (vía Labs, knime.yml, pixi): https://docs.knime.com/latest/pure_python_node_extensions_guide/
- Código fuente de NodeFactory de KNIME (la única abstracción genérica de nodo): https://github.com/knime/knime-core/blob/master/org.knime.core/src/eclipse/org/knime/core/node/NodeFactory.java
- Orange: Widget Development, Getting Started: https://orange3.readthedocs.io/projects/orange-development/en/latest/tutorial.html
- Orange: Tutorial (construcción manual de la GUI con `gui.spin`, `gui.checkBox`, etc.): https://orange3.readthedocs.io/projects/orange-development/en/latest/tutorial-settings.html
- Orange: referencia de OWWidget (la única abstracción genérica de widget): https://orange3.readthedocs.io/projects/orange-development/en/latest/widget.html
- WEKA: "Making a Weka classifier" (blog oficial de WEKA: recorrido por AbstractClassifier, y el mecanismo `GenericObjectEditor`/`@OptionMetadata` que autogenera parcialmente la UI de la hoja de propiedades a partir de anotaciones): https://waikato.github.io/weka-blog/posts/2018-10-08-making-a-weka-classifier/
- WEKA: Javadoc de AbstractClassifier (clase y contratos de los métodos `buildClassifier(Instances)` y `distributionForInstance(Instance)`): https://weka.sourceforge.io/doc.dev/weka/classifiers/AbstractClassifier.html
- WEKA: Javadoc de Filter (abstracción base para la familia de filtros): https://weka.sourceforge.io/doc.dev/weka/filters/Filter.html
- WEKA: seis jerarquías abstractas de nivel superior confirmadas contra la estructura del repositorio (`weka.classifiers.AbstractClassifier`, `weka.clusterers.AbstractClusterer`, `weka.associations.AbstractAssociator`, `weka.filters.Filter`, `weka.attributeSelection.ASEvaluation`, `weka.core.converters.AbstractLoader`): https://github.com/Waikato/weka-3.8/tree/master
- dashAI: referencia de API de clases abstractas (12 clases base): https://docs.dash-ai.com/api/back.html
- dashAI: profundización en arquitectura (FastAPI/React, autogeneración de Pydantic a JSON Schema): https://docs.dash-ai.com/deep-dive/architecture/

**Arquitectura de la interfaz**

- KNIME sobre Eclipse: https://www.knime.com/open-source-story
- Orange sobre PyQt: https://github.com/biolab/orange3
- WEKA Explorer extiende `javax.swing.JPanel` (Javadoc): https://weka.sourceforge.io/doc.stable/weka/gui/explorer/Explorer.html
- Arquitectura cliente-servidor de dashAI: https://docs.dash-ai.com/deep-dive/architecture/

**Catálogo nativo**
Los conteos del catálogo (modelos por tarea, soporte GPU, disponibilidad multilingüe, frameworks de HPO) se obtuvieron mediante inspección directa de la propia interfaz de cada plataforma (repositorio de nodos de KNIME, catálogo de widgets de Orange, Explorer/Package Manager de WEKA, y catálogo de modelos de dashAI), en lugar de a partir de un único listado externo, ya que ninguna de las cuatro plataformas publica un conteo autoritativo desglosado exactamente de esta manera.
