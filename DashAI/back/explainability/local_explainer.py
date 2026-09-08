from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Final, List, Optional, Tuple

from DashAI.back.config_object import ConfigObject
from DashAI.back.core.artifacts import ArtifactGroup, GroupedArtifacts
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.base_model import BaseModel

if TYPE_CHECKING:
    from datasets import DatasetDict


class BaseLocalExplainer(ConfigObject, ABC):
    """Abstract base class for instance-level (local) model explainability methods.

    Local explainers explain individual predictions: given a single input example,
    they attribute the model's output to specific feature values for that instance.
    Unlike global explainers (which average over the full dataset), local
    explanations can reveal why the model made a particular decision for a
    specific sample and can differ substantially from sample to sample.

    Concrete implementations must provide :meth:`fit` (prepare background data or
    internal state), :meth:`explain_instance` (compute per-instance attributions),
    and :meth:`plot` (turn explanations into renderable artifacts).
    """

    TYPE: Final[str] = "LocalExplainer"

    def __init__(self, model: BaseModel) -> None:
        """Initialise the local explainer with the model to be explained.

        Parameters
        ----------
        model : BaseModel
            The trained DashAI model whose predictions will be explained.
        """
        self.model = model
        self.explanation = None

    def fit(self, dataset: Tuple["DatasetDict", "DatasetDict"], *args, **kwargs):
        """Fit the explainer on the full dataset (optional pre-computation step).

        The default implementation is a no-op that simply returns ``self``.
        Subclasses may override this method to pre-compute any background data
        or internal state required before calling :meth:`explain_instance`.

        Parameters
        ----------
        dataset : Tuple[DatasetDict, DatasetDict]
            A two-element tuple ``(x, y)`` containing the full dataset splits
            used to fit or calibrate the explainer.
        *args : Any
            Additional positional arguments passed to concrete implementations.
        **kwargs : Any
            Additional keyword arguments passed to concrete implementations.

        Returns
        -------
        BaseLocalExplainer
            The fitted explainer instance (``self``).
        """
        return self

    @abstractmethod
    def explain_instance(self, instances: "DatasetDict") -> dict:
        """Compute a local explanation for the given instances.

        Concrete implementations must produce a per-instance explanation that
        describes how the model arrived at its prediction for each input.

        Parameters
        ----------
        instances : DatasetDict
            One or more instances to explain, provided as a ``DatasetDict``
            containing the input features.

        Returns
        -------
        dict
            A dictionary of explanation data for the provided instances.
            The exact keys depend on the explainer, but typically include
            feature attributions or importance scores for each instance.

        Raises
        ------
        NotImplementedError
            If the subclass does not provide an implementation.
        """
        raise NotImplementedError

    def story(
        self, explanation: dict, explainer_output: ArtifactGroup
    ) -> Optional[MultilingualString]:
        """Generate a narrative summary for one explained instance.

        Optional hook: explainers that can describe an instance's explanation
        in words should override this method and return a deterministic
        narrative (derived from the same ``explanation`` dict used by
        :meth:`plot`, available in every supported language). The default
        implementation reports that no narrative is available for this
        explainer.

        Parameters
        ----------
        explanation : dict
            The explanation dictionary produced by :meth:`explain_instance`.
        explainer_output : ArtifactGroup
            The group previously returned by :meth:`plot` for the instance
            being described.

        Returns
        -------
        Optional[MultilingualString]
            The narrative in every supported language, or ``None`` if this
            explainer does not implement one.
        """
        return None

    @abstractmethod
    def plot(self, explanation: dict) -> List[GroupedArtifacts]:
        """Generate renderable artifacts from a previously computed explanation.

        Concrete implementations must convert the explanation dictionary
        returned by :meth:`explain_instance` into typed artifacts that can be
        rendered on the frontend. Local explainers typically return a single
        :class:`GroupedArtifacts` whose groups are one explained instance each
        (the frontend renders its selector as the explained rows picker).

        Parameters
        ----------
        explanation : dict
            The explanation dictionary produced by :meth:`explain_instance`.

        Returns
        -------
        List[GroupedArtifacts]
            A list containing a single grouped artifact whose groups
            are one explained instance each.

        Raises
        ------
        NotImplementedError
            If the subclass does not provide an implementation.
        """
        raise NotImplementedError
