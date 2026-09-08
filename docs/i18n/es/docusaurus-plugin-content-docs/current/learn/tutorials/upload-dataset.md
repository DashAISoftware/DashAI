---
title: Cargar un dataset
sidebar_label: Cargar un dataset
---

# Cargar un dataset

Este tutorial te guía a través del proceso de carga de un dataset en dashAI.
Cargar un dataset es siempre el primer paso. Una vez cargado, queda disponible
en toda la plataforma para exploración, preprocesamiento y entrenamiento de modelos.

## Formatos compatibles

| Formato | Dataloader        | Extensión       |
| ------- | ----------------- | --------------- |
| CSV     | `CSVDataLoader`   | `.csv`          |
| Excel   | `ExcelDataLoader` | `.xlsx`, `.xls` |
| JSON    | `JSONDataLoader`  | `.json`         |

---

## Guía paso a paso

### 1. Abrir la sección de Datasets

En la barra de navegación superior, haz clic en **DATASETS**.
En el área principal, haz clic en la opción **"Upload Dataset"** en el centro de la pantalla.

Esto abre el flujo de carga en línea, así que permaneces en la misma pantalla durante todo el proceso.

### 2. Seleccionar un Dataloader

Aparece un panel con la lista de dataloaders disponibles, cada uno con una breve descripción
del formato de archivo que maneja.

Haz clic en el dataloader que corresponda a tu archivo (p. ej., **CSVDataLoader**) y haz clic en **"Next"**.

:::tip ¿Qué es un Dataloader?
Un Dataloader es el componente que sabe cómo leer un formato de archivo específico.
Seleccionar el correcto garantiza que dashAI pueda analizar tu archivo correctamente y exponer
los parámetros de configuración adecuados para ese formato.
:::

### 3. Cargar tu archivo

Una vez seleccionado el dataloader, el botón de carga de archivos se habilita.
Haz clic en **"Upload a File"** y selecciona tu archivo de dataset desde tu computadora.

Después de que el archivo sea procesado, dashAI muestra una **Vista previa del dataset** en el centro de la pantalla.

---

### 4. Revisar la vista previa del dataset

La tabla de vista previa muestra las primeras 5 filas de una **muestra de 100 filas** tomada de tu archivo.
Esta muestra es utilizada por dashAI para inferir automáticamente el tipo de datos de cada columna.

```
Mostrando 100 de 1000 filas analizadas para inferencia de tipos.
Puedes cambiar los tipos de columna haciendo clic en el menú desplegable de cada encabezado de columna.
```

**Editar tipos de columna**

Cada encabezado de columna tiene un menú desplegable que muestra el tipo inferido. Haz clic en él para cambiarlo manualmente:

| Tipo          | Cuándo usarlo                                                                                            |
| ------------- | -------------------------------------------------------------------------------------------------------- |
| `Categorical` | Valores discretos que representan grupos o etiquetas (p. ej., género, nivel educativo, tipo de vivienda) |
| `Float`       | Números continuos con decimales (p. ej., ingresos, precio, proporción)                                   |
| `Integer`     | Números enteros sin decimales (p. ej., edad, conteo, años de experiencia)                                |
| `Text`        | Contenido en lenguaje natural libre (p. ej., comentarios, descripciones, reseñas)                        |

Revisar y corregir los tipos de columna en esta etapa garantiza que la plataforma interprete
tus datos correctamente en cada paso posterior.

:::note Volver a cargar
Si necesitas reemplazar el archivo después de ver la vista previa, haz clic en el botón
**"RE-UPLOAD DATASET"** encima de la tabla de vista previa. Esto te lleva de vuelta al paso de
selección de archivo sin perder tu configuración de parámetros actual.
:::

---

### 5. Configurar los parámetros

El panel derecho está dividido en dos secciones: **Type Inference Configuration**
y **Dataloader Configuration**. Ambas afectan cómo se lee y almacena el dataset.

#### Configuración de inferencia de tipos

Esta sección aparece para todos los dataloaders.

| Parámetro          | Tipo   | Descripción                                                                                                                                                                                                                                                                                       |
| ------------------ | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Inference Rows** | Entero | El número de filas que dashAI lee para determinar automáticamente el tipo de datos de cada columna. El valor predeterminado es `1000`. Aumentar este valor mejora la precisión de la inferencia en datasets con valores inconsistentes o mixtos, a costa de un tiempo de carga ligeramente mayor. |

#### Configuración del Dataloader

Los parámetros de esta sección dependen del dataloader que hayas seleccionado.

---

**CSVDataLoader**

| Parámetro     | Tipo          | Descripción                                                                                                                                                                                                                                                                  |
| ------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Name**      | Cadena        | El nombre que identificará este dataset dentro de dashAI. Se rellena previamente con el nombre de tu archivo, y puedes cambiarlo aquí.                                                                                                                                       |
| **Separator** | Desplegable   | El carácter que separa los valores de las columnas en tu CSV. El valor predeterminado es `,` (coma). Cambia a `;` (punto y coma) para archivos exportados desde Excel en configuraciones regionales en español o europeas, donde la coma es el separador decimal.            |
| **Header**    | Cadena        | Cómo dashAI identifica la fila que contiene los nombres de las columnas. El valor predeterminado `infer` lo detecta automáticamente (generalmente la primera fila). Establece un número de fila explícito si tu archivo tiene líneas de metadatos antes del encabezado real. |
| **Names**     | Cadena / Null | Lista opcional de nombres de columna para asignar manualmente, reemplazando los nombres encontrados en el archivo. Deja como `Null` para usar los nombres de columna propios del archivo.                                                                                    |
| **Encoding**  | Desplegable   | Codificación de caracteres de tu archivo. El valor predeterminado es `utf-8`. Cambia a `latin-1` o `ISO-8859-1` si los caracteres especiales (acentos, símbolos) aparecen distorsionados después de la carga.                                                                |
| **NA values** | Cadena / Null | Cadenas adicionales para tratar como valores faltantes. Por ejemplo, `"?"` o `"N/A"`. Deja como `Null` para usar el comportamiento predeterminado.                                                                                                                           |

---

**JSONDataLoader**

| Parámetro    | Tipo   | Descripción                                                                                                                                                                                                                                                         |
| ------------ | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Name**     | Cadena | El nombre que identificará este dataset dentro de dashAI. Se rellena previamente con el nombre de tu archivo, y puedes cambiarlo aquí.                                                                                                                              |
| **Data key** | Cadena | La clave dentro de tu archivo JSON que contiene los registros de datos reales. El valor predeterminado es `data`. Cambia esto para que coincida con la clave de tu archivo donde se encuentran las filas o registros (p. ej., `"results"`, `"records"`, `"items"`). |

:::note Estructura JSON
dashAI espera que tu archivo JSON contenga un objeto de nivel superior con una clave que apunte a
un arreglo de registros. Por ejemplo: `{ "data": [ {...}, {...} ] }`.
Si tus datos están almacenados bajo una clave diferente, establece **Data key** según corresponda.
:::

---

**ExcelDataLoader**

| Parámetro           | Tipo          | Descripción                                                                                                                                                                                                                                               |
| ------------------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Name**            | Cadena        | El nombre que identificará este dataset dentro de dashAI. Se rellena previamente con el nombre de tu archivo, y puedes cambiarlo aquí.                                                                                                                    |
| **Sheet**           | Entero        | El índice de la hoja a cargar, comenzando en `0`. El valor predeterminado es `0` (la primera hoja). Cámbialo si tus datos están en una hoja diferente.                                                                                                    |
| **Header**          | Entero / Null | El número de fila (indexado desde cero) que contiene los nombres de las columnas. El valor predeterminado es `0` (primera fila). Establece en `Null` si tu archivo no tiene fila de encabezado.                                                           |
| **Use columns**     | Cadena / Null | Especifica qué columnas cargar. Deja como `Null` para cargar todas las columnas. Puedes ingresar una lista separada por comas de nombres o índices de columnas para cargar solo columnas específicas.                                                     |
| **Skip rows**       | Entero / Null | Número de filas a omitir al inicio de la hoja antes de leer. Útil si tu archivo Excel tiene filas de título, encabezados de informe o líneas en blanco antes de los datos. Deja como `Null` para no omitir nada.                                          |
| **N rows**          | Entero / Null | Número máximo de filas a cargar. Deja como `Null` para cargar toda la hoja. Útil para probar con un archivo grande.                                                                                                                                       |
| **Names**           | Cadena / Null | Lista opcional de nombres de columna para asignar manualmente. Deja como `Null` para usar los nombres de columna encontrados en el archivo.                                                                                                               |
| **NA values**       | Cadena / Null | Cadenas adicionales para tratar como valores faltantes. Deja como `Null` para usar el comportamiento predeterminado.                                                                                                                                      |
| **Keep default NA** | Casilla       | Cuando está habilitado (valor predeterminado), dashAI reconoce una lista integrada de cadenas NA comunes (`"NA"`, `"NaN"`, `"null"`, cadenas vacías, etc.) como valores faltantes automáticamente. Deshabilita solo si necesitas control manual completo. |
| **True values**     | Cadena / Null | Cadenas para interpretar como `True` booleano (p. ej., `"yes"`, `"Y"`, `"1"`). Deja como `Null` si tus datos no tienen columnas booleanas codificadas como texto.                                                                                         |
| **False values**    | Cadena / Null | Cadenas para interpretar como `False` booleano (p. ej., `"no"`, `"N"`, `"0"`). Deja como `Null` si no aplica.                                                                                                                                             |

:::note Keep default NA + NA values
Estos dos parámetros funcionan juntos. Cuando **Keep default NA** está habilitado y también
defines **NA values** personalizados, ambos conjuntos se combinan, y tus cadenas personalizadas se agregan
encima de los valores predeterminados. Deshabilitar **Keep default NA** significa que solo tus cadenas
definidas explícitamente serán tratadas como faltantes.
:::

---

### 6. Cargar el dataset

Una vez que hayas revisado los tipos de columna y configurado los parámetros, haz clic en **"UPLOAD"**
para finalizar el proceso.

dashAI procesará el archivo y lo agregará a la lista de **Available Datasets** en la barra lateral
izquierda, mostrando el número total de filas y columnas.

Haz clic en **"BACK"** en cualquier momento para volver al paso anterior sin perder tu configuración.

---

## Consejos

- Después de cargar, usa el módulo **Explorations** para verificar visualmente que las columnas
  se cargaron correctamente antes de ejecutar cualquier experimento.
- Si una columna numérica aparece como `Categorical`, probablemente contiene caracteres no numéricos
  (espacios, símbolos o valores mixtos), así que revisa el archivo fuente y vuelve a cargarlo después de limpiar.
- Usa el parámetro **N rows** (disponible en algunos dataloaders) para cargar solo una parte
  de un archivo grande mientras pruebas tu configuración.
- El parámetro **Separator** es la fuente más común de errores de carga de una sola columna
  en archivos CSV. Si tu dataset aparece como una columna larga, esto es lo primero que debes verificar.

## Solución de problemas

| Síntoma                                                     | Causa probable                                        | Solución                                                            |
| ----------------------------------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------- |
| El dataset se carga como una sola columna                   | Separador incorrecto seleccionado (CSV)               | Haz clic en **RE-UPLOAD DATASET** y establece el separador correcto |
| Una columna numérica aparece como `Categorical`             | La columna contiene caracteres no numéricos           | Corrige el archivo fuente y vuelve a cargarlo                       |
| Los caracteres especiales aparecen distorsionados           | Codificación incorrecta (CSV)                         | Cambia **Encoding** a `latin-1` o `ISO-8859-1`                      |
| Los nombres de columna son incorrectos o faltan             | La fila de encabezado no está en la posición esperada | Ajusta el parámetro **Header** al índice de fila correcto           |
| Se cargó la hoja incorrecta (Excel)                         | El índice de hoja predeterminado es `0`               | Cambia el parámetro **Sheet** al índice correcto                    |
| Filas adicionales en la parte superior de los datos (Excel) | El archivo tiene filas de título/metadatos            | Usa **Skip rows** para omitirlas                                    |
| Los valores NA no se reconocen como faltantes               | Cadenas NA personalizadas no definidas                | Agrega tus cadenas NA en el campo **NA values**                     |
| JSON se carga con columnas incorrectas                      | Los datos están bajo una clave diferente              | Establece **Data key** con la clave correcta en tu estructura JSON  |
