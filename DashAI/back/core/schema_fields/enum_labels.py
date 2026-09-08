"""What a dropdown option is called, for the option sets that repeat.

An enum's values are the vocabulary of the library underneath: ``friedman_mse``,
``char_wb``, ``balanced_subsample``, ``C`` and ``F``. Those are the right values
to send and the wrong words to show, and until ``enum_field`` gained a ``labels``
argument the renderer had no choice but to display them raw, in every language.

Most of those vocabularies are shared. 216 unlabelled enum fields use only 110
distinct option sets, and ``["sqrt", "log2"]`` means the same thing in every
component that offers it. So the label belongs to the option set rather than to
the field, and lives here once instead of at each of the call sites.

``enum_field`` consults this table when a schema passes no ``labels`` of its own,
so a component gets the shared names by declaring nothing, and can still override
them by passing ``labels`` explicitly.

Two rules for adding an entry:

* **Only register a set whose meaning is the same everywhere it appears.**
  ``("auto",)`` is deliberately absent: it is offered by ``iterated_power``,
  where it means "pick the iteration count for me", and by
  ``sampling_strategy``, where it means "resample every class but the largest".
  One label cannot be right for both, so those keep their raw value and the
  field's description carries the meaning.
* **Do not label what already reads as words.** ``["add", "subtract",
  "multiply", "divide"]`` and ``["black", "white", "blur"]`` are already the
  clearest thing to show. Device lists and model checkpoints are the same case:
  ``sentence-transformers/all-MiniLM-L6-v2`` is the identifier a user wants to
  see, and renaming it would be a loss.
"""

from typing import Dict, Tuple

from DashAI.back.core.utils import MultilingualString

__all__ = ["SHARED_ENUM_LABELS", "labels_for"]


def _m(en: str, es: str, pt: str, de: str, zh: str) -> MultilingualString:
    return MultilingualString(en=en, es=es, pt=pt, de=de, zh=zh)


#: Option names shared by every field that offers the same option set.
SHARED_ENUM_LABELS: Dict[Tuple[str, ...], Dict[str, MultilingualString]] = {
    # -- scikit-learn: class weighting ------------------------------------- #
    ("balanced",): {
        "balanced": _m(
            "Weighted by inverse class frequency",
            "Ponderado por la frecuencia inversa de clase",
            "Ponderado pela frequência inversa da classe",
            "Gewichtet nach inverser Klassenhäufigkeit",
            "按类别频率的倒数加权",
        ),
    },
    ("balanced", "balanced_subsample"): {
        "balanced": _m(
            "Weighted by inverse class frequency",
            "Ponderado por la frecuencia inversa de clase",
            "Ponderado pela frequência inversa da classe",
            "Gewichtet nach inverser Klassenhäufigkeit",
            "按类别频率的倒数加权",
        ),
        "balanced_subsample": _m(
            "Reweighted for every tree's sample",
            "Reponderado para la muestra de cada árbol",
            "Reponderado para a amostra de cada árvore",
            "Für die Stichprobe jedes Baums neu gewichtet",
            "为每棵树的样本重新加权",
        ),
    },
    # -- the sentinel that stands for an object a form cannot express ------- #
    ("RandomState",): {
        "RandomState": _m(
            "A new random generator each run",
            "Un generador aleatorio nuevo en cada ejecución",
            "Um novo gerador aleatório a cada execução",
            "Bei jedem Lauf ein neuer Zufallsgenerator",
            "每次运行使用新的随机生成器",
        ),
    },
    # -- feature subsets --------------------------------------------------- #
    ("sqrt", "log2"): {
        "sqrt": _m(
            "Square root of the feature count",
            "Raíz cuadrada del número de características",
            "Raiz quadrada do número de características",
            "Quadratwurzel der Merkmalsanzahl",
            "特征数的平方根",
        ),
        "log2": _m(
            "Base-2 logarithm of the feature count",
            "Logaritmo en base 2 del número de características",
            "Logaritmo de base 2 do número de características",
            "Logarithmus zur Basis 2 der Merkmalsanzahl",
            "特征数的以2为底的对数",
        ),
    },
    # -- nearest neighbours ------------------------------------------------ #
    ("uniform", "distance"): {
        "uniform": _m(
            "Every neighbour counts the same",
            "Todos los vecinos pesan igual",
            "Todos os vizinhos pesam igual",
            "Alle Nachbarn zählen gleich",
            "所有邻居权重相同",
        ),
        "distance": _m(
            "Closer neighbours count more",
            "Los vecinos más cercanos pesan más",
            "Vizinhos mais próximos pesam mais",
            "Nähere Nachbarn zählen mehr",
            "越近的邻居权重越大",
        ),
    },
    ("auto", "ball_tree", "kd_tree", "brute"): {
        "auto": _m(
            "Chosen from the data",
            "Elegido a partir de los datos",
            "Escolhido a partir dos dados",
            "Anhand der Daten gewählt",
            "根据数据自动选择",
        ),
        "ball_tree": _m("Ball tree", "Ball tree", "Ball tree", "Ball-Baum", "球树"),
        "kd_tree": _m("k-d tree", "Árbol k-d", "Árvore k-d", "k-d-Baum", "k-d 树"),
        "brute": _m(
            "Brute force", "Fuerza bruta", "Força bruta", "Brute Force", "暴力搜索"
        ),
    },
    # -- language codes ---------------------------------------------------- #
    ("en", "es", "pt"): {
        "en": _m("English", "Inglés", "Inglês", "Englisch", "英语"),
        "es": _m("Spanish", "Español", "Espanhol", "Spanisch", "西班牙语"),
        "pt": _m("Portuguese", "Portugués", "Português", "Portugiesisch", "葡萄牙语"),
    },
    # -- distance metrics, where three names mean the same thing ----------- #
    ("cityblock", "cosine", "euclidean", "l1", "l2", "manhattan"): {
        "cityblock": _m(
            "Manhattan distance",
            "Distancia Manhattan",
            "Distância de Manhattan",
            "Manhattan-Distanz",
            "曼哈顿距离",
        ),
        "cosine": _m(
            "Cosine distance",
            "Distancia del coseno",
            "Distância do cosseno",
            "Kosinus-Distanz",
            "余弦距离",
        ),
        "euclidean": _m(
            "Euclidean distance",
            "Distancia euclidiana",
            "Distância euclidiana",
            "Euklidische Distanz",
            "欧几里得距离",
        ),
        "l1": _m(
            "Manhattan distance (L1)",
            "Distancia Manhattan (L1)",
            "Distância de Manhattan (L1)",
            "Manhattan-Distanz (L1)",
            "曼哈顿距离 (L1)",
        ),
        "l2": _m(
            "Euclidean distance (L2)",
            "Distancia euclidiana (L2)",
            "Distância euclidiana (L2)",
            "Euklidische Distanz (L2)",
            "欧几里得距离 (L2)",
        ),
        "manhattan": _m(
            "Manhattan distance",
            "Distancia Manhattan",
            "Distância de Manhattan",
            "Manhattan-Distanz",
            "曼哈顿距离",
        ),
    },
    # -- time series components -------------------------------------------- #
    ("none", "add", "mul"): {
        "none": _m("None", "Ninguno", "Nenhum", "Keine", "无"),
        "add": _m("Additive", "Aditivo", "Aditivo", "Additiv", "加法"),
        "mul": _m(
            "Multiplicative",
            "Multiplicativo",
            "Multiplicativo",
            "Multiplikativ",
            "乘法",
        ),
    },
    # -- kernel coefficient ------------------------------------------------ #
    ("scale", "auto"): {
        "scale": _m(
            "Scaled by the feature variance",
            "Escalado por la varianza de las características",
            "Escalado pela variância das características",
            "Nach der Merkmalsvarianz skaliert",
            "按特征方差缩放",
        ),
        "auto": _m(
            "One over the feature count",
            "Uno dividido por el número de características",
            "Um dividido pelo número de características",
            "Eins geteilt durch die Merkmalsanzahl",
            "特征数的倒数",
        ),
    },
    # -- plotly ------------------------------------------------------------ #
    ("all", "outliers", "False"): {
        "all": _m(
            "Every point",
            "Todos los puntos",
            "Todos os pontos",
            "Alle Punkte",
            "所有点",
        ),
        "outliers": _m(
            "Outliers only",
            "Solo los valores atípicos",
            "Apenas os valores atípicos",
            "Nur Ausreißer",
            "仅离群点",
        ),
        "False": _m(
            "No points", "Ningún punto", "Nenhum ponto", "Keine Punkte", "不显示点"
        ),
    },
    ("count", "sum", "avg", "min", "max"): {
        "count": _m("Count", "Recuento", "Contagem", "Anzahl", "计数"),
        "sum": _m("Sum", "Suma", "Soma", "Summe", "求和"),
        "avg": _m("Average", "Promedio", "Média", "Durchschnitt", "平均值"),
        "min": _m("Minimum", "Mínimo", "Mínimo", "Minimum", "最小值"),
        "max": _m("Maximum", "Máximo", "Máximo", "Maximum", "最大值"),
    },
    ("none", "percent", "probability"): {
        "none": _m("Raw counts", "Recuentos", "Contagens", "Rohe Anzahl", "原始计数"),
        "percent": _m("Percent", "Porcentaje", "Porcentagem", "Prozent", "百分比"),
        "probability": _m(
            "Probability", "Probabilidad", "Probabilidade", "Wahrscheinlichkeit", "概率"
        ),
    },
    # -- numpy dtypes and memory order ------------------------------------- #
    ("int32", "int64"): {
        "int32": _m(
            "32-bit integer",
            "Entero de 32 bits",
            "Inteiro de 32 bits",
            "32-Bit-Ganzzahl",
            "32 位整数",
        ),
        "int64": _m(
            "64-bit integer",
            "Entero de 64 bits",
            "Inteiro de 64 bits",
            "64-Bit-Ganzzahl",
            "64 位整数",
        ),
    },
    ("C", "F"): {
        "C": _m(
            "Row-major order (C)",
            "Orden por filas (C)",
            "Ordem por linhas (C)",
            "Zeilenweise Anordnung (C)",
            "行优先顺序 (C)",
        ),
        "F": _m(
            "Column-major order (Fortran)",
            "Orden por columnas (Fortran)",
            "Ordem por colunas (Fortran)",
            "Spaltenweise Anordnung (Fortran)",
            "列优先顺序 (Fortran)",
        ),
    },
    ("np.nan",): {
        "np.nan": _m(
            "Not a number (NaN)",
            "No es un número (NaN)",
            "Não é um número (NaN)",
            "Keine Zahl (NaN)",
            "非数值 (NaN)",
        ),
    },
    # -- text vectorizing -------------------------------------------------- #
    ("english",): {
        "english": _m(
            "English stop words",
            "Palabras vacías en inglés",
            "Palavras vazias em inglês",
            "Englische Stoppwörter",
            "英语停用词",
        ),
    },
    ("word", "char", "char_wb"): {
        "word": _m("Words", "Palabras", "Palavras", "Wörter", "词"),
        "char": _m("Characters", "Caracteres", "Caracteres", "Zeichen", "字符"),
        "char_wb": _m(
            "Characters, without crossing word boundaries",
            "Caracteres, sin cruzar los límites de palabra",
            "Caracteres, sem cruzar os limites das palavras",
            "Zeichen, ohne Wortgrenzen zu überschreiten",
            "字符，不跨越词边界",
        ),
    },
    ("ascii", "unicode"): {
        "ascii": _m(
            "Strip accents, ASCII only",
            "Quitar acentos, solo ASCII",
            "Remover acentos, apenas ASCII",
            "Akzente entfernen, nur ASCII",
            "去除重音，仅 ASCII",
        ),
        "unicode": _m(
            "Strip accents, any script",
            "Quitar acentos, cualquier alfabeto",
            "Remover acentos, qualquer alfabeto",
            "Akzente entfernen, jede Schrift",
            "去除重音，任意文字",
        ),
    },
    ("ascii", "unicode", "None"): {
        "ascii": _m(
            "Strip accents, ASCII only",
            "Quitar acentos, solo ASCII",
            "Remover acentos, apenas ASCII",
            "Akzente entfernen, nur ASCII",
            "去除重音，仅 ASCII",
        ),
        "unicode": _m(
            "Strip accents, any script",
            "Quitar acentos, cualquier alfabeto",
            "Remover acentos, qualquer alfabeto",
            "Akzente entfernen, jede Schrift",
            "去除重音，任意文字",
        ),
        "None": _m(
            "Keep accents",
            "Conservar los acentos",
            "Manter os acentos",
            "Akzente beibehalten",
            "保留重音",
        ),
    },
    ("l1", "l2", "None"): {
        "l1": _m(
            "L1 (sum of absolute values)",
            "L1 (suma de valores absolutos)",
            "L1 (soma dos valores absolutos)",
            "L1 (Summe der Absolutwerte)",
            "L1（绝对值之和）",
        ),
        "l2": _m(
            "L2 (Euclidean length)",
            "L2 (longitud euclidiana)",
            "L2 (comprimento euclidiano)",
            "L2 (euklidische Länge)",
            "L2（欧几里得长度）",
        ),
        "None": _m(
            "No normalization",
            "Sin normalización",
            "Sem normalização",
            "Keine Normalisierung",
            "不归一化",
        ),
    },
    ("l1", "l2", "max"): {
        "l1": _m(
            "L1 (sum of absolute values)",
            "L1 (suma de valores absolutos)",
            "L1 (soma dos valores absolutos)",
            "L1 (Summe der Absolutwerte)",
            "L1（绝对值之和）",
        ),
        "l2": _m(
            "L2 (Euclidean length)",
            "L2 (longitud euclidiana)",
            "L2 (comprimento euclidiano)",
            "L2 (euklidische Länge)",
            "L2（欧几里得长度）",
        ),
        "max": _m(
            "Largest absolute value",
            "Mayor valor absoluto",
            "Maior valor absoluto",
            "Größter Absolutwert",
            "最大绝对值",
        ),
    },
    # -- unseen categories -------------------------------------------------- #
    ("error", "ignore", "infrequent_if_exist"): {
        "error": _m(
            "Raise an error",
            "Lanzar un error",
            "Lançar um erro",
            "Fehler auslösen",
            "抛出错误",
        ),
        "ignore": _m(
            "Encode as all zeros",
            "Codificar como todo ceros",
            "Codificar como zeros",
            "Als lauter Nullen kodieren",
            "编码为全零",
        ),
        "infrequent_if_exist": _m(
            "Fold into the infrequent category",
            "Agrupar en la categoría poco frecuente",
            "Agrupar na categoria pouco frequente",
            "Der seltenen Kategorie zuordnen",
            "归入低频类别",
        ),
    },
    ("error", "use_encoded_value"): {
        "error": _m(
            "Raise an error",
            "Lanzar un error",
            "Lançar um erro",
            "Fehler auslösen",
            "抛出错误",
        ),
        "use_encoded_value": _m(
            "Use the fallback value below",
            "Usar el valor de reemplazo de abajo",
            "Usar o valor de substituição abaixo",
            "Den unten angegebenen Ersatzwert verwenden",
            "使用下面的替代值",
        ),
    },
    # -- imputation --------------------------------------------------------- #
    ("mean", "median", "most_frequent", "constant"): {
        "mean": _m(
            "Column mean",
            "Media de la columna",
            "Média da coluna",
            "Spaltenmittelwert",
            "列均值",
        ),
        "median": _m(
            "Column median",
            "Mediana de la columna",
            "Mediana da coluna",
            "Spaltenmedian",
            "列中位数",
        ),
        "most_frequent": _m(
            "Most frequent value",
            "Valor más frecuente",
            "Valor mais frequente",
            "Häufigster Wert",
            "最常见值",
        ),
        "constant": _m(
            "A fixed value",
            "Un valor fijo",
            "Um valor fixo",
            "Ein fester Wert",
            "固定值",
        ),
    },
    ("nan_euclidean",): {
        "nan_euclidean": _m(
            "Euclidean distance, ignoring missing values",
            "Distancia euclidiana, ignorando los valores faltantes",
            "Distância euclidiana, ignorando os valores ausentes",
            "Euklidische Distanz, fehlende Werte ignoriert",
            "欧几里得距离，忽略缺失值",
        ),
    },
    # -- losses and split criteria ------------------------------------------ #
    ("linear", "square", "exponential"): {
        "linear": _m("Linear", "Lineal", "Linear", "Linear", "线性"),
        "square": _m("Squared", "Cuadrática", "Quadrática", "Quadratisch", "平方"),
        "exponential": _m(
            "Exponential", "Exponencial", "Exponencial", "Exponentiell", "指数"
        ),
    },
    ("log_loss", "exponential"): {
        "log_loss": _m(
            "Log loss",
            "Pérdida logarítmica",
            "Perda logarítmica",
            "Log-Loss",
            "对数损失",
        ),
        "exponential": _m(
            "Exponential (AdaBoost)",
            "Exponencial (AdaBoost)",
            "Exponencial (AdaBoost)",
            "Exponentiell (AdaBoost)",
            "指数 (AdaBoost)",
        ),
    },
    ("squared_error", "absolute_error", "huber", "quantile"): {
        "squared_error": _m(
            "Squared error",
            "Error cuadrático",
            "Erro quadrático",
            "Quadratischer Fehler",
            "平方误差",
        ),
        "absolute_error": _m(
            "Absolute error",
            "Error absoluto",
            "Erro absoluto",
            "Absoluter Fehler",
            "绝对误差",
        ),
        "huber": _m(
            "Huber (robust to outliers)",
            "Huber (robusta ante atípicos)",
            "Huber (robusta a atípicos)",
            "Huber (robust gegen Ausreißer)",
            "Huber（对离群点稳健）",
        ),
        "quantile": _m("Quantile", "Cuantil", "Quantil", "Quantil", "分位数"),
    },
    ("friedman_mse", "squared_error"): {
        "friedman_mse": _m(
            "Friedman's mean squared error",
            "Error cuadrático medio de Friedman",
            "Erro quadrático médio de Friedman",
            "Friedmans mittlerer quadratischer Fehler",
            "Friedman 均方误差",
        ),
        "squared_error": _m(
            "Mean squared error",
            "Error cuadrático medio",
            "Erro quadrático médio",
            "Mittlerer quadratischer Fehler",
            "均方误差",
        ),
    },
    ("entropy", "gini", "log_loss"): {
        "entropy": _m("Entropy", "Entropía", "Entropia", "Entropie", "熵"),
        "gini": _m(
            "Gini impurity",
            "Impureza de Gini",
            "Impureza de Gini",
            "Gini-Unreinheit",
            "基尼不纯度",
        ),
        "log_loss": _m(
            "Log loss",
            "Pérdida logarítmica",
            "Perda logarítmica",
            "Log-Loss",
            "对数损失",
        ),
    },
    ("most_frequent", "prior", "stratified", "uniform"): {
        "most_frequent": _m(
            "Always the most frequent class",
            "Siempre la clase más frecuente",
            "Sempre a classe mais frequente",
            "Immer die häufigste Klasse",
            "始终预测最常见类别",
        ),
        "prior": _m(
            "The class prior",
            "La probabilidad a priori de la clase",
            "A probabilidade a priori da classe",
            "Die A-priori-Klassenwahrscheinlichkeit",
            "类别先验概率",
        ),
        "stratified": _m(
            "Random, following the class distribution",
            "Aleatorio, siguiendo la distribución de clases",
            "Aleatório, seguindo a distribuição das classes",
            "Zufällig, gemäß der Klassenverteilung",
            "随机，遵循类别分布",
        ),
        "uniform": _m(
            "Random, all classes equally likely",
            "Aleatorio, todas las clases igual de probables",
            "Aleatório, todas as classes igualmente prováveis",
            "Zufällig, alle Klassen gleich wahrscheinlich",
            "随机，各类别等概率",
        ),
    },
    # -- feature selection --------------------------------------------------- #
    ("percentile", "k_best", "fpr", "fdr", "fwe"): {
        "percentile": _m(
            "Top percentile of features",
            "Percentil superior de características",
            "Percentil superior de características",
            "Oberstes Perzentil der Merkmale",
            "特征的最高百分位",
        ),
        "k_best": _m(
            "The k best features",
            "Las k mejores características",
            "As k melhores características",
            "Die k besten Merkmale",
            "最佳的 k 个特征",
        ),
        "fpr": _m(
            "False positive rate",
            "Tasa de falsos positivos",
            "Taxa de falsos positivos",
            "Falsch-Positiv-Rate",
            "假阳性率",
        ),
        "fdr": _m(
            "False discovery rate",
            "Tasa de falsos descubrimientos",
            "Taxa de falsas descobertas",
            "False-Discovery-Rate",
            "错误发现率",
        ),
        "fwe": _m(
            "Family-wise error rate",
            "Tasa de error por familia",
            "Taxa de erro por família",
            "Familienweise Fehlerrate",
            "族系误差率",
        ),
    },
    # -- decompositions ------------------------------------------------------ #
    ("parallel", "deflation"): {
        "parallel": _m(
            "All components at once",
            "Todos los componentes a la vez",
            "Todos os componentes de uma vez",
            "Alle Komponenten auf einmal",
            "同时提取所有成分",
        ),
        "deflation": _m(
            "One component at a time",
            "Un componente a la vez",
            "Um componente de cada vez",
            "Eine Komponente nach der anderen",
            "逐个提取成分",
        ),
    },
    ("logcosh", "exp", "cube"): {
        "logcosh": _m("log cosh", "log cosh", "log cosh", "log cosh", "log cosh"),
        "exp": _m("Exponential", "Exponencial", "Exponencial", "Exponentiell", "指数"),
        "cube": _m("Cube", "Cubo", "Cubo", "Kubisch", "立方"),
    },
    ("eigh", "svd"): {
        "eigh": _m(
            "Eigenvalue decomposition",
            "Descomposición en valores propios",
            "Decomposição em autovalores",
            "Eigenwertzerlegung",
            "特征值分解",
        ),
        "svd": _m(
            "Singular value decomposition",
            "Descomposición en valores singulares",
            "Decomposição em valores singulares",
            "Singulärwertzerlegung",
            "奇异值分解",
        ),
    },
    ("arpack", "randomized"): {
        "arpack": _m(
            "ARPACK (exact, iterative)",
            "ARPACK (exacto, iterativo)",
            "ARPACK (exato, iterativo)",
            "ARPACK (exakt, iterativ)",
            "ARPACK（精确、迭代）",
        ),
        "randomized": _m(
            "Randomized (faster, approximate)",
            "Aleatorizado (más rápido, aproximado)",
            "Aleatorizado (mais rápido, aproximado)",
            "Randomisiert (schneller, näherungsweise)",
            "随机化（更快、近似）",
        ),
    },
    ("mle",): {
        "mle": _m(
            "Guessed from the data (Minka's MLE)",
            "Estimado a partir de los datos (MLE de Minka)",
            "Estimado a partir dos dados (MLE de Minka)",
            "Aus den Daten geschätzt (Minkas MLE)",
            "由数据估计（Minka 的 MLE）",
        ),
    },
    # -- token pooling ------------------------------------------------------- #
    ("mean", "max"): {
        "mean": _m(
            "Average of the tokens",
            "Promedio de los tokens",
            "Média dos tokens",
            "Durchschnitt der Token",
            "词元的平均值",
        ),
        "max": _m(
            "Largest value per dimension",
            "Mayor valor por dimensión",
            "Maior valor por dimensão",
            "Größter Wert je Dimension",
            "每个维度的最大值",
        ),
    },
    ("mean", "cls", "max"): {
        "mean": _m(
            "Average of the tokens",
            "Promedio de los tokens",
            "Média dos tokens",
            "Durchschnitt der Token",
            "词元的平均值",
        ),
        "cls": _m(
            "The CLS token",
            "El token CLS",
            "O token CLS",
            "Das CLS-Token",
            "CLS 词元",
        ),
        "max": _m(
            "Largest value per dimension",
            "Mayor valor por dimensión",
            "Maior valor por dimensão",
            "Größter Wert je Dimension",
            "每个维度的最大值",
        ),
    },
    # -- hyperparameters that became searchable -------------------------------
    #
    # These sets were unlabelled while their fields were plain dropdowns. They
    # are now declared as categorical search spaces, so the same vocabulary is
    # also what the "options to search" control lists, which is where a raw
    # `squared_epsilon_insensitive` is least readable.
    ("squared_hinge", "hinge"): {
        "squared_hinge": _m(
            "Squared hinge",
            "Bisagra cuadrática",
            "Dobradiça quadrática",
            "Quadratischer Hinge-Verlust",
            "平方铰链损失",
        ),
        "hinge": _m("Hinge", "Bisagra", "Dobradiça", "Hinge-Verlust", "铰链损失"),
    },
    ("hinge", "log_loss", "modified_huber", "squared_hinge", "perceptron"): {
        "hinge": _m(
            "Hinge (linear SVM)",
            "Bisagra (SVM lineal)",
            "Dobradiça (SVM linear)",
            "Hinge-Verlust (lineare SVM)",
            "铰链损失（线性 SVM）",
        ),
        "log_loss": _m(
            "Log loss (logistic regression)",
            "Pérdida logarítmica (regresión logística)",
            "Perda logarítmica (regressão logística)",
            "Log-Loss (logistische Regression)",
            "对数损失（逻辑回归）",
        ),
        "modified_huber": _m(
            "Modified Huber, tolerant to outliers",
            "Huber modificada, tolerante a valores atípicos",
            "Huber modificada, tolerante a valores atípicos",
            "Modifizierter Huber, robust gegen Ausreißer",
            "改进的 Huber 损失，对异常值稳健",
        ),
        "squared_hinge": _m(
            "Squared hinge",
            "Bisagra cuadrática",
            "Dobradiça quadrática",
            "Quadratischer Hinge-Verlust",
            "平方铰链损失",
        ),
        "perceptron": _m(
            "Perceptron", "Perceptrón", "Perceptron", "Perzeptron", "感知机"
        ),
    },
    ("epsilon_insensitive", "squared_epsilon_insensitive"): {
        "epsilon_insensitive": _m(
            "Epsilon-insensitive",
            "Insensible a epsilon",
            "Insensível a epsilon",
            "Epsilon-insensitiv",
            "对 epsilon 不敏感",
        ),
        "squared_epsilon_insensitive": _m(
            "Squared epsilon-insensitive",
            "Insensible a epsilon, al cuadrado",
            "Insensível a epsilon, ao quadrado",
            "Quadratisch epsilon-insensitiv",
            "对 epsilon 不敏感（平方）",
        ),
    },
    ("l2", "l1", "elasticnet"): {
        "l2": _m(
            "L2, ridge",
            "L2, ridge",
            "L2, ridge",
            "L2, Ridge",
            "L2（岭）",
        ),
        "l1": _m(
            "L1, lasso, drives coefficients to zero",
            "L1, lasso, lleva coeficientes a cero",
            "L1, lasso, leva coeficientes a zero",
            "L1, Lasso, setzt Koeffizienten auf null",
            "L1（套索），将系数压缩为零",
        ),
        "elasticnet": _m(
            "Elastic net, a mix of L1 and L2",
            "Elastic net, una mezcla de L1 y L2",
            "Elastic net, uma mistura de L1 e L2",
            "Elastic Net, eine Mischung aus L1 und L2",
            "弹性网络，L1 与 L2 的混合",
        ),
    },
    ("adam", "lbfgs", "sgd"): {
        "adam": _m("Adam", "Adam", "Adam", "Adam", "Adam"),
        "lbfgs": _m("L-BFGS", "L-BFGS", "L-BFGS", "L-BFGS", "L-BFGS"),
        "sgd": _m(
            "Stochastic gradient descent",
            "Descenso de gradiente estocástico",
            "Descida de gradiente estocástica",
            "Stochastischer Gradientenabstieg",
            "随机梯度下降",
        ),
    },
    ("squared_error", "absolute_error", "poisson"): {
        "squared_error": _m(
            "Squared error",
            "Error cuadrático",
            "Erro quadrático",
            "Quadratischer Fehler",
            "平方误差",
        ),
        "absolute_error": _m(
            "Absolute error",
            "Error absoluto",
            "Erro absoluto",
            "Absoluter Fehler",
            "绝对误差",
        ),
        "poisson": _m(
            "Poisson deviance, for counts",
            "Desviación de Poisson, para conteos",
            "Desvio de Poisson, para contagens",
            "Poisson-Abweichung, für Zähldaten",
            "泊松偏差，用于计数数据",
        ),
    },
    ("minkowski", "euclidean", "manhattan", "chebyshev"): {
        "minkowski": _m(
            "Minkowski", "Minkowski", "Minkowski", "Minkowski", "闵可夫斯基距离"
        ),
        "euclidean": _m(
            "Euclidean, straight-line",
            "Euclidiana, en línea recta",
            "Euclidiana, em linha reta",
            "Euklidisch, Luftlinie",
            "欧几里得距离（直线）",
        ),
        "manhattan": _m(
            "Manhattan, along the axes",
            "Manhattan, a lo largo de los ejes",
            "Manhattan, ao longo dos eixos",
            "Manhattan, entlang der Achsen",
            "曼哈顿距离（沿坐标轴）",
        ),
        "chebyshev": _m(
            "Chebyshev, the largest single difference",
            "Chebyshev, la mayor diferencia individual",
            "Chebyshev, a maior diferença individual",
            "Tschebyschow, die größte Einzeldifferenz",
            "切比雪夫距离（最大单一差值）",
        ),
    },
    ("relu", "tanh", "logistic", "identity"): {
        "relu": _m("ReLU", "ReLU", "ReLU", "ReLU", "ReLU"),
        "tanh": _m(
            "Hyperbolic tangent",
            "Tangente hiperbólica",
            "Tangente hiperbólica",
            "Tangens hyperbolicus",
            "双曲正切",
        ),
        "logistic": _m(
            "Logistic, sigmoid",
            "Logística, sigmoide",
            "Logística, sigmoide",
            "Logistisch, Sigmoid",
            "逻辑函数（S 形）",
        ),
        "identity": _m(
            "Identity, no activation",
            "Identidad, sin activación",
            "Identidade, sem ativação",
            "Identität, keine Aktivierung",
            "恒等函数（无激活）",
        ),
    },
    ("relu", "tanh", "sigmoid", "identity"): {
        "relu": _m("ReLU", "ReLU", "ReLU", "ReLU", "ReLU"),
        "tanh": _m(
            "Hyperbolic tangent",
            "Tangente hiperbólica",
            "Tangente hiperbólica",
            "Tangens hyperbolicus",
            "双曲正切",
        ),
        "sigmoid": _m("Sigmoid", "Sigmoide", "Sigmoide", "Sigmoid", "S 形函数"),
        "identity": _m(
            "Identity, no activation",
            "Identidad, sin activación",
            "Identidade, sem ativação",
            "Identität, keine Aktivierung",
            "恒等函数（无激活）",
        ),
    },
    ("constant", "optimal", "invscaling", "adaptive"): {
        "constant": _m("Constant", "Constante", "Constante", "Konstant", "恒定"),
        "optimal": _m(
            "Optimal, from a heuristic schedule",
            "Óptima, según una regla heurística",
            "Ótima, segundo uma regra heurística",
            "Optimal, nach einem heuristischen Zeitplan",
            "最优（依启发式调度）",
        ),
        "invscaling": _m(
            "Decaying with each step",
            "Decreciente en cada paso",
            "Decrescente a cada passo",
            "Mit jedem Schritt abnehmend",
            "随步数衰减",
        ),
        "adaptive": _m(
            "Adaptive, drops when progress stalls",
            "Adaptativa, baja cuando el avance se estanca",
            "Adaptativa, cai quando o progresso estagna",
            "Adaptiv, sinkt bei stagnierendem Fortschritt",
            "自适应，进展停滞时下降",
        ),
    },
    ("linear", "poly", "rbf", "sigmoid"): {
        "linear": _m("Linear", "Lineal", "Linear", "Linear", "线性"),
        "poly": _m("Polynomial", "Polinomial", "Polinomial", "Polynomial", "多项式"),
        "rbf": _m(
            "Radial basis function",
            "Función de base radial",
            "Função de base radial",
            "Radiale Basisfunktion",
            "径向基函数",
        ),
        "sigmoid": _m("Sigmoid", "Sigmoide", "Sigmoide", "Sigmoid", "S 形函数"),
    },
    ("rbf", "linear", "poly", "sigmoid"): {
        "rbf": _m(
            "Radial basis function",
            "Función de base radial",
            "Função de base radial",
            "Radiale Basisfunktion",
            "径向基函数",
        ),
        "linear": _m("Linear", "Lineal", "Linear", "Linear", "线性"),
        "poly": _m("Polynomial", "Polinomial", "Polinomial", "Polynomial", "多项式"),
        "sigmoid": _m("Sigmoid", "Sigmoide", "Sigmoide", "Sigmoid", "S 形函数"),
    },
    ("auto", "svd", "cholesky", "lsqr", "sparse_cg", "sag", "saga"): {
        "auto": _m(
            "Chosen automatically",
            "Elegido automáticamente",
            "Escolhido automaticamente",
            "Automatisch gewählt",
            "自动选择",
        ),
        "svd": _m(
            "Singular value decomposition",
            "Descomposición en valores singulares",
            "Decomposição em valores singulares",
            "Singulärwertzerlegung",
            "奇异值分解",
        ),
        "cholesky": _m("Cholesky", "Cholesky", "Cholesky", "Cholesky", "乔列斯基分解"),
        "lsqr": _m(
            "Least squares, iterative",
            "Mínimos cuadrados, iterativo",
            "Mínimos quadrados, iterativo",
            "Kleinste Quadrate, iterativ",
            "最小二乘（迭代）",
        ),
        "sparse_cg": _m(
            "Conjugate gradient, for sparse data",
            "Gradiente conjugado, para datos dispersos",
            "Gradiente conjugado, para dados esparsos",
            "Konjugierter Gradient, für dünn besetzte Daten",
            "共轭梯度，用于稀疏数据",
        ),
        "sag": _m(
            "Stochastic average gradient",
            "Gradiente promedio estocástico",
            "Gradiente médio estocástico",
            "Stochastischer Durchschnittsgradient",
            "随机平均梯度",
        ),
        "saga": _m(
            "SAGA, a variant of stochastic average gradient",
            "SAGA, una variante del gradiente promedio estocástico",
            "SAGA, uma variante do gradiente médio estocástico",
            "SAGA, eine Variante des stochastischen Durchschnittsgradienten",
            "SAGA，随机平均梯度的变体",
        ),
    },
}


def labels_for(enum) -> Dict[str, MultilingualString]:
    """The shared names for an option set, or an empty mapping if there are none.

    Parameters
    ----------
    enum : sequence
        The option values, in the order the field declares them.

    Returns
    -------
    dict
        Option to name. Empty when the set is not registered, which is the
        common case and means the raw values are shown.
    """
    try:
        return SHARED_ENUM_LABELS.get(tuple(enum), {})
    except TypeError:
        # An unhashable member cannot be a dropdown option anyway.
        return {}
