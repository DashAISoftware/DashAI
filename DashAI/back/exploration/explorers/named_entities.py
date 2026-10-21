"""People, organizations and places named in text items."""

from collections import Counter
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from DashAI.back.converters.hugging_face.pretrained_tool import (
    PretrainedTool,
    batches,
    device_field,
)
from DashAI.back.core.data_kinds import DATASET, DOCUMENT
from DashAI.back.core.schema_fields import float_field, int_field, schema_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Explorer
from DashAI.back.dependencies.downloads.downloadable import HFDownloadableMixin
from DashAI.back.exploration.base_explorer import BaseExplorerSchema
from DashAI.back.exploration.text_analysis_explorer import TextAnalysisExplorer
from DashAI.back.models.utils import DEVICE_PLACEHOLDER
from DashAI.back.types.value_types import Text

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

ENTITY_TYPES = {"PER": "Person", "ORG": "Organization", "LOC": "Location"}
BATCH_SIZE = 8
STRIDE = 64


class NamedEntitiesSchema(BaseExplorerSchema):
    """Schema for the named entities explorer."""

    top_n: schema_field(
        int_field(ge=1, le=200),
        20,
        description=MultilingualString(
            en="How many entities to show, between 1 and 200.",
            es="Cuántas entidades mostrar, entre 1 y 200.",
            pt="Quantas entidades mostrar, entre 1 e 200.",
            de="Wie viele Entitäten angezeigt werden, zwischen 1 und 200.",
            zh="显示的实体数量，介于 1 和 200 之间。",
        ),
        alias=MultilingualString(
            en="Entities shown",
            es="Entidades mostradas",
            pt="Entidades mostradas",
            de="Angezeigte Entitäten",
            zh="显示的实体",
        ),
    )  # type: ignore
    min_score: schema_field(
        float_field(ge=0.0, le=1.0),
        0.6,
        description=MultilingualString(
            en="Lowest model confidence, between 0 and 1, for an entity to count.",
            es="Confianza mínima del modelo, entre 0 y 1, para contar una entidad.",
            pt="Confiança mínima do modelo, entre 0 e 1, para contar uma entidade.",
            de=(
                "Niedrigste Modellsicherheit zwischen 0 und 1, ab der eine Entität "
                "zählt."
            ),
            zh="实体被计入所需的最低模型置信度（0 到 1）。",
        ),
        alias=MultilingualString(
            en="Minimum confidence",
            es="Confianza mínima",
            pt="Confiança mínima",
            de="Mindestsicherheit",
            zh="最低置信度",
        ),
    )  # type: ignore
    device: device_field()  # type: ignore


class NamedEntitiesExplorer(TextAnalysisExplorer, PretrainedTool):
    """Find the people, organizations and places named in text items.

    Uses ``Davlan/xlm-roberta-base-ner-hrl``, trained on ten languages
    including English, Spanish, Portuguese, German, French and Chinese.
    Entities are counted by their text and type; the chart shows the most
    frequent ones next to a table with counts and types.
    """

    SCHEMA = NamedEntitiesSchema
    MODEL_NAME = "Davlan/xlm-roberta-base-ner-hrl"
    HF_IGNORE_PATTERNS = [*HFDownloadableMixin.HF_IGNORE_PATTERNS, "*.bin"]
    DOWNLOAD_SIZE_BYTES = 1114942833
    DISPLAY_NAME = MultilingualString(
        en="Named Entities",
        es="Entidades Nombradas",
        pt="Entidades Nomeadas",
        de="Benannte Entitäten",
        zh="命名实体",
    )
    DESCRIPTION = MultilingualString(
        en="Finds and counts the people, organizations and places named in text.",
        es="Encuentra y cuenta las personas, organizaciones y lugares nombrados.",
        pt="Encontra e conta as pessoas, organizações e lugares mencionados.",
        de="Findet und zählt die im Text genannten Personen, Organisationen und Orte.",
        zh="查找并统计文本中提到的人物、组织和地点。",
    )
    metadata: Dict[str, Any] = {
        "allowed_types": [Text],
        "allowed_dtypes": [],
        "input_cardinality": {"exact": 1},
        "data_kinds": [DATASET, DOCUMENT],
    }

    def __init__(self, **kwargs) -> None:
        """Store the options and the device.

        Parameters
        ----------
        **kwargs
            ``top_n``, ``min_score`` and ``device`` from
            ``NamedEntitiesSchema``.
        """
        self.top_n = kwargs.get("top_n", 20)
        self.min_score = kwargs.get("min_score", 0.6)
        self.setup_device(kwargs.get("device", DEVICE_PLACEHOLDER))
        super().__init__(**kwargs)

    def load_pretrained(self, source: str) -> Any:
        """Load the token classification pipeline.

        Parameters
        ----------
        source : str
            A local directory or the Hub repo id.

        Returns
        -------
        transformers.Pipeline
            A pipeline that groups word pieces into whole entities.
        """
        from transformers import pipeline

        return pipeline(
            "token-classification",
            model=source,
            aggregation_strategy="simple",
            device=self.device,
            stride=STRIDE,
        )

    def find_entities(self, values: List[str]) -> List[Tuple[str, str]]:
        """Return the confident entities of the texts.

        Parameters
        ----------
        values : List[str]
            The texts.

        Returns
        -------
        List[Tuple[str, str]]
            ``(entity text, type label)`` for every confident mention.
        """
        finder = self.pretrained()
        texts = [value for value in values if value.strip()]
        found: List[Tuple[str, str]] = []
        for batch in batches(texts, BATCH_SIZE):
            for mentions in finder(batch):
                for mention in mentions:
                    word = " ".join(mention["word"].split())
                    if mention["score"] >= self.min_score and len(word) > 1:
                        group = mention["entity_group"]
                        found.append((word, ENTITY_TYPES.get(group, group)))
        return found

    def launch_exploration(
        self, dataset: "DashAIDataset", explorer_info: Explorer
    ) -> Any:
        """Build a table and a bar chart of the most named entities.

        Parameters
        ----------
        dataset : DashAIDataset
            The selected text.
        explorer_info : Explorer
            The explorer record.

        Returns
        -------
        plotly.graph_objects.Figure
            The entity table above the bar chart.
        """
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        counts = Counter(self.find_entities(self.text_column(dataset, explorer_info)))
        top = counts.most_common(self.top_n)
        figure = make_subplots(
            rows=2,
            cols=1,
            specs=[[{"type": "table"}], [{}]],
            subplot_titles=["Entities", "Most named"],
            vertical_spacing=0.08,
        )
        figure.add_trace(
            go.Table(
                header={"values": ["Entity", "Type", "Mentions"]},
                cells={
                    "values": [
                        [entity for (entity, _), _ in top],
                        [kind for (_, kind), _ in top],
                        [count for _, count in top],
                    ]
                },
            ),
            row=1,
            col=1,
        )
        for kind in sorted({kind for (_, kind), _ in top}):
            chosen = [(entity, count) for (entity, k), count in top if k == kind]
            figure.add_trace(
                go.Bar(
                    x=[count for _, count in chosen],
                    y=[entity for entity, _ in chosen],
                    orientation="h",
                    name=kind,
                ),
                row=2,
                col=1,
            )
        figure.update_yaxes(autorange="reversed", row=2, col=1)
        figure.update_layout(
            title=explorer_info.name or "Named entities",
            height=max(700, 30 * len(top) + 500),
        )
        if not top:
            figure.add_annotation(
                text="No entities found.",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.25,
            )
        return figure
