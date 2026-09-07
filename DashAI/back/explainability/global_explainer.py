from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Final, List, Optional, Tuple, Union

from DashAI.back.config_object import ConfigObject
from DashAI.back.core.artifacts import Artifact, ArtifactGroup, GroupedArtifacts
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.base_model import BaseModel

if TYPE_CHECKING:
    from datasets import DatasetDict


class BaseGlobalExplainer(ConfigObject, ABC):
    """Abstract base class for global model explainability methods.

    Global explainers analyse the behaviour of a trained model across an entire
    dataset, producing explanations that describe which features are most
    influential *on average* (as opposed to local explainers, which explain a
    single prediction). Typical outputs include feature-importance rankings,
    partial dependence curves, or aggregate attribution scores.

    All concrete global explainers must implement :meth:`explain` (compute the
    explanation from a dataset) and :meth:`plot` (turn the explanation into
    renderable artifacts for the frontend).
    """

    TYPE: Final[str] = "GlobalExplainer"

    def __init__(self, model: BaseModel) -> None:
        """Initialise the global explainer with the model to be explained.

        Parameters
        ----------
        model : BaseModel
            The trained DashAI model whose predictions will be explained.
        """
        self.model = model

    @abstractmethod
    def explain(self, dataset: Tuple["DatasetDict", "DatasetDict"]) -> dict:
        """Compute a global explanation for the given dataset.

        Concrete implementations must analyse the model's behaviour across
        the full dataset and return a structured explanation dictionary.

        Parameters
        ----------
        dataset : Tuple[DatasetDict, DatasetDict]
            A two-element tuple ``(x, y)`` where ``x`` contains the input
            splits (e.g. ``x["test"]``) and ``y`` contains the corresponding
            target splits.

        Returns
        -------
        dict
            A dictionary of explanation data.  The exact keys depend on the
            explainer, but typically include feature names and their associated
            importance scores (e.g. ``"features"``, ``"importances_mean"``,
            ``"importances_std"``).

        Raises
        ------
        NotImplementedError
            If the subclass does not provide an implementation.
        """
        raise NotImplementedError

    def story(
        self, explanation: dict, explainer_output: Union[Artifact, ArtifactGroup]
    ) -> Optional[MultilingualString]:
        """Generate a narrative summary for one artifact of the explanation.

        Optional hook: explainers that can describe their explanation in
        words should override this method and return a deterministic
        narrative (derived from the same ``explanation`` dict used by
        :meth:`plot`, available in every supported language). The default
        implementation reports that no narrative is available for this
        explainer.

        Parameters
        ----------
        explanation : dict
            The explanation dictionary produced by :meth:`explain`.
        explainer_output : Union[Artifact, ArtifactGroup]
            One of the artifacts (or artifact groups) previously returned by
            :meth:`plot`, identifying which part of the explanation the
            narrative should describe.

        Returns
        -------
        Optional[MultilingualString]
            The narrative in every supported language, or ``None`` if this
            explainer does not implement one.
        """
        return None

    @abstractmethod
    def plot(self, explanation: dict) -> List[Union[Artifact, GroupedArtifacts]]:
        """Generate renderable artifacts from a previously computed explanation.

        Concrete implementations must convert the explanation dictionary
        returned by :meth:`explain` into one or more typed artifacts that
        can be rendered on the frontend.

        Parameters
        ----------
        explanation : dict
            The explanation dictionary produced by :meth:`explain`.

        Returns
        -------
        List[Union[Artifact, GroupedArtifacts]]
            A list of artifacts (:class:`PlotlyArtifact`,
            :class:`TableArtifact`, :class:`TextArtifact` or
            :class:`ImageArtifact`) and/or :class:`GroupedArtifacts` batches
            (e.g. a summary table next to its plot for one curve/count) that
            the frontend should render together, describing the explanation.

        Raises
        ------
        NotImplementedError
            If the subclass does not provide an implementation.
        """
        raise NotImplementedError
