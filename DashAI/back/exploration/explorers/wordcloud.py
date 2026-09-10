from typing import TYPE_CHECKING, Any, Dict, List

from DashAI.back.core.artifacts import Artifact, ImageArtifact, ImagePayload
from DashAI.back.core.schema_fields import (
    int_field,
    none_type,
    schema_field,
    string_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Explorer, Notebook
from DashAI.back.exploration.base_explorer import BaseExplorerSchema
from DashAI.back.exploration.distribution_explorer import DistributionExplorer
from DashAI.back.types.value_types import Text

if TYPE_CHECKING:
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class WordcloudSchema(BaseExplorerSchema):
    """Schema for WordcloudExplorer hyperparameters.

    Configures the vocabulary size cap (``max_words``) and the background colour
    of the word cloud image. All text columns to concatenate are selected via
    the base schema's column-selection mechanism.
    """

    max_words: schema_field(
        t=int_field(gt=0),
        placeholder=200,
        description=MultilingualString(
            en="Maximum number of words to display in the word cloud.",
            es="Número máximo de palabras a mostrar en la nube de palabras.",
            pt="Número máximo de palavras a exibir na nuvem de palavras.",
            zh="词云中显示的最大词数。",
            de="Maximale Anzahl der anzuzeigenden Wörter in der Wortwolke.",
        ),
        alias=MultilingualString(
            en="Max words",
            es="Máximo de palabras",
            pt="Máximo de palavras",
            zh="最大词数",
            de="Max. Wörter",
        ),
    )  # type: ignore
    background_color: schema_field(
        t=none_type(string_field()),
        placeholder=None,
        description=MultilingualString(
            en=(
                "Background color of the word cloud. If None, the background is "
                "transparent."
            ),
            es=(
                "Color de fondo de la nube de palabras. Si es None, el fondo es "
                "transparente."
            ),
            pt=("Cor de fundo da nuvem de palavras. Se None, o fundo é transparente."),
            zh="词云的背景颜色。如果为None，则背景透明。",
            de=(
                "Hintergrundfarbe der Wortwolke. Bei None ist der Hintergrund "
                "transparent."
            ),
        ),
        alias=MultilingualString(
            en="Background color",
            es="Color de fondo",
            pt="Cor de fundo",
            zh="背景颜色",
            de="Hintergrundfarbe",
        ),
    )  # type: ignore


class WordcloudExplorer(DistributionExplorer):
    """Visualise word frequency in text columns as a word cloud.

    Concatenates the values of all selected text columns across every row of the
    dataset and produces a word cloud image where each word is rendered at a
    size proportional to its term frequency. Stop words are not removed
    automatically; preprocessing should be applied via converters before
    running this explorer if stop-word filtering is desired.

    Word clouds are a quick way to identify the most common terms in a text
    corpus, detect vocabulary overlap between classes, and communicate the
    dominant topics in a dataset to non-technical audiences.
    """

    DISPLAY_NAME = MultilingualString(
        en="Word Cloud",
        es="Nube de Palabras",
        pt="Nuvem de Palavras",
        zh="词云",
        de="Wortwolke",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Visual representation of text where word size reflects frequency. "
            "Generates a word cloud by concatenating selected text columns."
        ),
        es=(
            "Representación visual del texto donde el tamaño de la palabra "
            "refleja su frecuencia. Genera una nube de palabras concatenando "
            "columnas de texto seleccionadas."
        ),
        pt=(
            "Representação visual do texto onde o tamanho da palavra "
            "reflete sua frequência. Gera uma nuvem de palavras concatenando "
            "colunas de texto selecionadas."
        ),
        zh=("文本的可视化表示，词语大小反映频率。通过连接所选文本列生成词云。"),
        de=(
            "Visuelle Darstellung von Text, bei der die Wortgröße die Häufigkeit "
            "widerspiegelt. Erzeugt eine Wortwolke durch Verkettung ausgewählter "
            "Textspalten."
        ),
    )
    IMAGE_PREVIEW = "wordcloud.png"

    SCHEMA = WordcloudSchema
    metadata: Dict[str, Any] = {
        "allowed_types": [Text],
        "allowed_dtypes": [],
        "input_cardinality": {"min": 1},
    }

    def __init__(self, **kwargs) -> None:
        """Initialize WordcloudExplorer with word cloud rendering parameters.

        Parameters
        ----------
        **kwargs
            Keyword arguments matching ``WordcloudSchema`` fields:
            max_words (int): Maximum number of words to display in the
            word cloud. Defaults to ``200``.
            background_color (str | None): Background color of the
            rendered image. When ``None`` the background is
            transparent (RGBA mode). Defaults to ``None``.
        """
        self.max_words = kwargs.get("max_words", 200)
        self.background_color = kwargs.get("background_color")
        super().__init__(**kwargs)

    def launch_exploration(self, dataset: "DashAIDataset", explorer_info: Explorer):
        """Generate a word cloud image from the selected text columns.

        Concatenates all values from the selected columns into a single string,
        removes common stop words, and renders a ``WordCloud`` image with the
        configured parameters.

        Parameters
        ----------
        dataset : DashAIDataset
            The dataset containing the text columns.
        explorer_info : Explorer
            The explorer database record used to
            determine which columns to concatenate.

        Returns
        -------
        Any
            A ``PIL.Image.Image`` of the rendered word cloud (PNG-compatible,
            RGBA when ``background_color`` is ``None``, RGB otherwise).
        """
        from wordcloud import STOPWORDS, WordCloud

        _df = dataset.to_pandas()
        cols = [col["columnName"] for col in explorer_info.columns]

        # concatenate all columns into one string
        text = " ".join(_df[cols].astype(str).sum(axis=1))

        # create wordcloud
        wordcloud = WordCloud(
            max_words=self.max_words,
            stopwords=STOPWORDS,
            background_color=self.background_color,
            mode="RGBA" if self.background_color is None else "RGB",
            width=800,
            height=600,
        ).generate(text)

        return wordcloud.to_image()

    def save_notebook(
        self,
        __exploration_info__: Notebook,
        explorer_info: Explorer,
        save_path: "Path",
        result: Any,
    ) -> str:
        """Save the word cloud PIL image to a PNG file on disk.

        Parameters
        ----------
        __exploration_info__ : Notebook
            The notebook database record
            (unused).
        explorer_info : Explorer
            The explorer record used for filename
            generation.
        save_path : Path
            Directory where the file will be saved.
        result : Any
            The ``PIL.Image.Image`` returned by
            ``launch_exploration``.

        Returns
        -------
        str
            The path of the saved PNG file as a POSIX string.
        """
        import os
        from pathlib import Path

        filename = f"{explorer_info.id}.png"
        path = Path(os.path.join(save_path, filename))
        result.save(path, format="PNG")

        return path.as_posix()

    def get_results(
        self, exploration_path: str, options: Dict[str, Any]
    ) -> List[Artifact]:
        """Load and return the saved word cloud image for the frontend.

        Reads the PNG file written by ``save_notebook`` and wraps its bytes
        in an image artifact.

        Parameters
        ----------
        exploration_path : str
            Path to the PNG file saved by ``save_notebook``.
        options : Dict[str, Any]
            Rendering options from the frontend (unused).

        Returns
        -------
        List[Artifact]
            A single-element list with the image artifact of the word
            cloud.
        """
        with open(exploration_path, "rb") as f:
            result = f.read()

        return [ImageArtifact(payload=ImagePayload(data=result))]
