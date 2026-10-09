"""Typed render artifacts shared by explainers and explorers.

An artifact is the unit of renderable output that a component (an explainer's
``plot`` method, an explorer's ``get_results`` method) hands to the frontend.
Every artifact serializes to the wire format::

    {"type": <str>, "payload": <Any>, "title": <Optional[str]>}

Supported types:

- ``"plotly"``: payload is a JSON string produced by ``plotly.io.to_json``.
- ``"table"``: payload is ``{"columns": List[str], "rows": List[List[Any]],
  "highlight": List[{"row": int, "column": int}]}``.
- ``"text"``: payload is a plain string rendered as preformatted text.
- ``"image"``: payload is ``{"data": <base64 str>, "mime": <str>}``.

A component may also return a :class:`GroupedArtifacts` alongside plain
artifacts. It bundles several :class:`ArtifactGroup` entries (each a titled
batch of leaf artifacts, e.g. a summary table next to its plot) into one
interactive selector: the frontend lists every group's title and shows one
group's artifacts at a time. It serializes to ``{"type": "grouped", "title":
<Optional[str]>, "groups": [{"title": <Optional[str]>, "artifacts": [<leaf
artifact dict>, ...]}, ...]}``; a group cannot itself contain another group.

Components created before this module returned other shapes: explainers
returned lists of plotly JSON strings, explorers returned a single
``{"data", "type", "config"}`` dict. :func:`normalize_artifacts` upgrades
both legacy shapes, so old pickled explanations, old saved explorations and
legacy plugin components keep working.
"""

import base64
import json
from typing import Annotated, Any, Dict, List, Literal, Optional, Union

from pydantic import (
    BaseModel,
    Field,
    TypeAdapter,
    ValidationError,
    field_validator,
    model_validator,
)


def _detect_mime(data: bytes) -> str:
    """Guess the MIME type of raw image bytes from their magic numbers.

    Parameters
    ----------
    data : bytes
        Raw image bytes.

    Returns
    -------
    str
        The detected MIME type, or ``"image/png"`` when unknown.
    """
    import filetype

    kind = filetype.guess(data)
    return kind.mime if kind is not None else "image/png"


class Artifact(BaseModel):
    """Base class for typed render artifacts.

    Attributes
    ----------
    type : str
        Discriminator naming the artifact kind; fixed per subclass.
    title : Optional[str]
        Human readable title shown above the rendered artifact.
    role : Literal["input", "explanation"]
        Role indicating artifact type, defaulting to explanation.
    """

    type: str
    title: Optional[str] = None
    role: Literal["input", "explanation"] = "explanation"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the artifact to its wire format.

        Returns
        -------
        Dict[str, Any]
            ``{"type", "payload", "title"}`` with a JSON-serializable payload.
        """
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Artifact":
        """Deserialize a wire format dict into the matching artifact subclass.

        Parameters
        ----------
        data : Dict[str, Any]
            A dict with ``type``, ``payload`` and optionally ``title``.

        Returns
        -------
        Artifact
            An instance of the subclass matching ``data["type"]``.

        Raises
        ------
        ValueError
            If the type is unknown or the payload is malformed.
        """
        try:
            return _ANY_ARTIFACT_ADAPTER.validate_python(data)
        except ValidationError as error:
            raise ValueError(f"Invalid artifact dict: {error}") from error


class PlotlyArtifact(Artifact):
    """Artifact holding a plotly figure serialized as JSON.

    Attributes
    ----------
    payload : str
        JSON string produced by ``plotly.io.to_json``. A live plotly
        ``Figure`` may be passed instead; it is serialized on validation.
    """

    type: Literal["plotly"] = "plotly"
    payload: str

    @field_validator("payload", mode="before")
    @classmethod
    def _serialize_figure(cls, value: Any) -> Any:
        if not isinstance(value, str) and hasattr(value, "to_plotly_json"):
            import plotly.io as pio

            return pio.to_json(value)
        return value


class TableCell(BaseModel):
    """Reference to a single table cell, 0-indexed relative to ``rows``.

    Attributes
    ----------
    row : int
        Row index of the cell.
    column : int
        Column index of the cell.
    """

    row: int = Field(ge=0)
    column: int = Field(ge=0)


class TablePayload(BaseModel):
    """Payload of a table artifact.

    Attributes
    ----------
    columns : List[str]
        Column headers.
    rows : List[List[Any]]
        Table rows; every row must have ``len(columns)`` cells.
    highlight : List[TableCell]
        Cells to emphasise when rendered.
    """

    columns: List[str]
    rows: List[List[Any]]
    highlight: List[TableCell] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_shape(self) -> "TablePayload":
        for i, row in enumerate(self.rows):
            if len(row) != len(self.columns):
                raise ValueError(
                    f"Row {i} has {len(row)} cells, expected {len(self.columns)}."
                )
        for cell in self.highlight:
            if cell.row >= len(self.rows) or cell.column >= len(self.columns):
                raise ValueError(
                    f"Highlight cell ({cell.row}, {cell.column}) is out of bounds."
                )
        return self


class TableArtifact(Artifact):
    """Artifact holding tabular data with optional highlighted cells.

    Attributes
    ----------
    payload : TablePayload
        Columns, rows and highlighted cells.
    """

    type: Literal["table"] = "table"
    payload: TablePayload


class TextArtifact(Artifact):
    """Artifact holding plain text rendered preformatted.

    Attributes
    ----------
    payload : str
        Text content; newlines are preserved when rendered.
    """

    type: Literal["text"] = "text"
    payload: str


class ImagePayload(BaseModel):
    """Payload of an image artifact.

    Attributes
    ----------
    data : str
        Base64-encoded image bytes. Raw ``bytes`` may be passed instead;
        they are encoded on validation.
    mime : str
        MIME type of the encoded image.
    """

    data: str
    mime: str = "image/png"

    @field_validator("data", mode="before")
    @classmethod
    def _encode_bytes(cls, value: Any) -> Any:
        if isinstance(value, (bytes, bytearray)):
            return base64.b64encode(bytes(value)).decode("ascii")
        if isinstance(value, str):
            try:
                base64.b64decode(value, validate=True)
            except Exception as error:
                raise ValueError("data is not valid base64.") from error
        return value


class ImageArtifact(Artifact):
    """Artifact holding a base64-encoded image.

    Attributes
    ----------
    payload : ImagePayload
        Base64 data and MIME type.
    """

    type: Literal["image"] = "image"
    payload: ImagePayload

    @classmethod
    def from_dashai_image(
        cls, image: Any, title: Optional[str] = None
    ) -> "ImageArtifact":
        """Build an image artifact from a dataset :class:`DashAIImage` value.

        Parameters
        ----------
        image : DashAIImage
            A dataset image instance carrying raw bytes.
        title : Optional[str]
            Human readable title shown above the artifact.

        Returns
        -------
        ImageArtifact
            The artifact wrapping the image bytes.

        Raises
        ------
        ValueError
            If the image has no bytes available.
        """
        if getattr(image, "bytes", None) is None:
            raise ValueError("DashAIImage has no bytes available.")
        return cls(
            payload=ImagePayload(data=image.bytes, mime=_detect_mime(image.bytes)),
            title=title,
        )


AnyArtifact = Annotated[
    Union[PlotlyArtifact, TableArtifact, TextArtifact, ImageArtifact],
    Field(discriminator="type"),
]

_ANY_ARTIFACT_ADAPTER: TypeAdapter = TypeAdapter(AnyArtifact)


class ArtifactGroup(BaseModel):
    """One selectable entry inside a :class:`GroupedArtifacts`.

    A group is a titled batch of leaf artifacts (e.g. a summary table next to
    its plot) shown together when its entry is selected. It cannot itself
    contain another group: ``artifacts`` is typed as leaf :data:`AnyArtifact`
    only.

    Attributes
    ----------
    title : Optional[str]
        Human readable label for this entry, shown as one row in the parent
        group's selector.
    artifacts : List[AnyArtifact]
        The leaf artifacts shown when this entry is selected, in display
        order.
    """

    title: Optional[str] = None
    artifacts: List[AnyArtifact]


class GroupedArtifacts(BaseModel):
    """A selector over several :class:`ArtifactGroup` entries.

    Lets a component (typically a global explainer producing one set of
    artifacts per curve/count) return a single interactive unit: the frontend
    renders a selector listing every group's title and shows one group's
    artifacts at a time. A component may return several ``GroupedArtifacts``
    in its ``plot`` output; each becomes its own independent selector.

    Attributes
    ----------
    title : Optional[str]
        Optional overall title for the selector.
    groups : List[ArtifactGroup]
        The selectable groups, in listing order.
    """

    type: Literal["grouped"] = "grouped"
    title: Optional[str] = None
    groups: List[ArtifactGroup]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the grouped artifacts to their wire format.

        Returns
        -------
        Dict[str, Any]
            ``{"type": "grouped", "title", "groups"}`` with each group's
            artifacts serialized to their own wire format dicts.
        """
        return self.model_dump()


AnyArtifactOrGroup = Annotated[
    Union[PlotlyArtifact, TableArtifact, TextArtifact, ImageArtifact, GroupedArtifacts],
    Field(discriminator="type"),
]


def _legacy_explorer_artifact(item: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a legacy explorer result dict into an artifact dict.

    Parameters
    ----------
    item : Dict[str, Any]
        A dict with the old explorer contract ``{"data", "type", "config"}``.

    Returns
    -------
    Dict[str, Any]
        The equivalent artifact dict; unknown legacy types degrade to a
        text artifact.
    """
    legacy_type = item.get("type")
    data = item.get("data")
    if legacy_type == "plotly_json" and isinstance(data, str):
        return PlotlyArtifact(payload=data).to_dict()
    if legacy_type == "tabular" and isinstance(data, dict):
        columns = ["index", *data.keys()]
        index_keys: List[Any] = []
        for column_values in data.values():
            if isinstance(column_values, dict):
                for key in column_values:
                    if key not in index_keys:
                        index_keys.append(key)
        rows = [
            [key, *(data[column].get(key) for column in data)] for key in index_keys
        ]
        return TableArtifact(payload=TablePayload(columns=columns, rows=rows)).to_dict()
    if legacy_type == "image_base64" and isinstance(data, str):
        return ImageArtifact(payload=ImagePayload(data=data)).to_dict()
    return TextArtifact(payload=str(data)).to_dict()


def normalize_artifacts(
    items: Any, *, create_grouped: bool = False
) -> List[Dict[str, Any]]:
    """Coerce any component output into a list of artifact/group wire dicts.

    Handles current values (``Artifact`` or :class:`GroupedArtifacts`
    instances, or their wire dicts) and legacy shapes: plain plotly JSON
    strings from old explainers, and ``{"data", "type", "config"}`` dicts
    from old explorers. Anything else is stringified into a text artifact so
    the frontend never receives an unrenderable value.

    Every leaf artifact, whether at the top level or nested inside a
    group's ``artifacts``, is stamped with a flat, sequential ``index`` so
    the frontend (and the plot override endpoints) can address any leaf by a
    single integer regardless of nesting depth.

    Parameters
    ----------
    items : Any
        The value returned by an explainer ``plot`` method, an explorer
        ``get_results`` method, or loaded from a persisted result file.
    create_grouped : bool, optional
        When ``True``, wrap a list of leaf artifacts into a single grouped
        artifact container with one selectable group per input item. This is
        useful for local explainers whose output is a list of per-instance
        artifacts.

    Returns
    -------
    List[Dict[str, Any]]
        A list of artifact/grouped wire dicts; leaf artifacts carry an
        ``"index"`` key. A grouped dict is
        ``{"type": "grouped", "title", "groups": [{"title", "artifacts"}]}``.
    """
    if items is None:
        return []
    if isinstance(items, (str, dict, Artifact, GroupedArtifacts)):
        items = [items]

    next_index = 0

    def normalize_leaf(item: Any) -> Dict[str, Any]:
        nonlocal next_index
        if isinstance(item, Artifact):
            data = item.to_dict()
        elif isinstance(item, str):
            data = PlotlyArtifact(payload=item).to_dict()
        elif isinstance(item, dict) and "type" in item and "payload" in item:
            data = {"title": None, "role": "explanation", **item}
        elif isinstance(item, dict) and "type" in item and "data" in item:
            data = _legacy_explorer_artifact(item)
        else:
            data = TextArtifact(payload=str(item)).to_dict()
        data["index"] = next_index
        next_index += 1
        return data

    def normalize_group(group: Any) -> Dict[str, Any]:
        if isinstance(group, ArtifactGroup):
            title, artifacts = group.title, group.artifacts
        else:
            title, artifacts = group.get("title"), group.get("artifacts", [])
        return {
            "title": title,
            "artifacts": [normalize_leaf(a) for a in artifacts],
        }

    def normalize_item(item: Any) -> Dict[str, Any]:
        if isinstance(item, GroupedArtifacts):
            return {
                "type": "grouped",
                "title": item.title,
                "groups": [normalize_group(g) for g in item.groups],
            }
        if isinstance(item, dict) and item.get("type") == "grouped":
            return {
                "type": "grouped",
                "title": item.get("title"),
                "groups": [normalize_group(g) for g in item.get("groups", [])],
            }
        return normalize_leaf(item)

    def is_grouped(value: Any) -> bool:
        return isinstance(value, GroupedArtifacts) or (
            isinstance(value, dict) and value.get("type") == "grouped"
        )

    # Migrate a flat list of per instance leaf artifacts (e.g. an old local
    # explainer's output) into a single grouped artifact with one selectable
    # group per instance. A payload that is already grouped is passed through
    # unchanged.
    if create_grouped and items and not is_grouped(items[0]):
        groups = [
            {"title": leaf.get("title"), "artifacts": [leaf]}
            for leaf in (normalize_leaf(item) for item in items)
        ]
        return [{"type": "grouped", "title": None, "groups": groups}]

    return [normalize_item(item) for item in items]


def build_tabular_input_artifact(
    feature_names: List[str],
    instance_values: List[Any],
    title: Optional[str] = None,
) -> "TableArtifact":
    """Build an input artifact holding one instance's feature values.

    Parameters
    ----------
    feature_names : List[str]
        Column headers, one per feature.
    instance_values : List[Any]
        The feature values fed to the model for this instance.
    title : Optional[str]
        Group title shared with the instance's explanation artifacts.

    Returns
    -------
    TableArtifact
        A single-row table artifact with role "input".
    """
    return TableArtifact(
        payload=TablePayload(
            columns=[str(name) for name in feature_names],
            rows=[list(instance_values)],
        ),
        title=title,
        role="input",
    )


def build_text_input_artifact(text: str, title: Optional[str] = None) -> "TextArtifact":
    """Build an input artifact holding the text fed to the model.

    Parameters
    ----------
    text : str
        The input text for this instance.
    title : Optional[str]
        Group title shared with the instance's explanation artifacts.

    Returns
    -------
    TextArtifact
        A text artifact with role "input".
    """
    return TextArtifact(payload=text, title=title, role="input")


def build_image_input_artifact(
    image: Any, title: Optional[str] = None
) -> "ImageArtifact":
    """Build an input artifact from the image fed to the model.

    Parameters
    ----------
    image : DashAIImage
        The input image instance for this explained sample.
    title : Optional[str]
        Group title shared with the instance's explanation artifacts.

    Returns
    -------
    ImageArtifact
        An image artifact with role "input".
    """
    artifact = ImageArtifact.from_dashai_image(image, title=title)
    artifact.role = "input"
    return artifact


class PlotOverrideBody(BaseModel):
    """Request body for saving one plot override.

    Parameters
    ----------
    index : int
        Artifact index whose payload is being overridden.
    figure : object
        The edited plotly figure, either a JSON string or a dict.
    """

    index: int
    figure: object


def apply_plot_overrides(
    artifacts: List[Dict[str, Any]], overrides: Optional[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Replace plotly artifact payloads with stored edited figures.

    Leaves nested inside a ``"grouped"`` selector (see
    :class:`GroupedArtifacts`), i.e. under each group's ``artifacts``, are
    matched by their stamped ``"index"`` just like top level ones, so a
    group's plotly artifact can be edited/reset the same way as a top level
    one.

    Parameters
    ----------
    artifacts : List[Dict[str, Any]]
        Normalized artifact/grouped dicts from :func:`normalize_artifacts`.
    overrides : Optional[Dict[str, Any]]
        Mapping of ``str(index)`` to an edited plotly figure (JSON string or
        dict).

    Returns
    -------
    List[Dict[str, Any]]
        The artifacts with overridden plotly payloads applied.
    """
    if not overrides:
        return artifacts

    leaves_by_index: Dict[Any, Dict[str, Any]] = {}

    def collect_leaves(items: List[Dict[str, Any]]) -> None:
        for item in items:
            if item.get("type") == "grouped":
                for group in item.get("groups", []):
                    collect_leaves(group.get("artifacts", []))
            else:
                leaves_by_index[item.get("index")] = item

    collect_leaves(artifacts)

    for key, figure in overrides.items():
        try:
            idx = int(key)
        except (TypeError, ValueError):
            continue
        leaf = leaves_by_index.get(idx)
        if leaf is not None and leaf.get("type") == "plotly":
            leaf["payload"] = figure if isinstance(figure, str) else json.dumps(figure)
            # Flag so the frontend renders the user's edited figure verbatim
            # instead of re-applying the app theme (which would clobber the
            # edited colors/background).
            leaf["overridden"] = True
    return artifacts
