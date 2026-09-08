from abc import ABCMeta, abstractmethod
from typing import Any, Dict

from DashAI.back.statistical_tests.statistical_test_result import StatisticalTestResult


class BaseStatisticalTest(metaclass=ABCMeta):
    """Abstract interface for all statistical tests used by the application.

    Concrete implementations define how a particular hypothesis test is executed
    and which metadata ispresented to the user. This class establishes the common
    contract shared by every statistical test so that they can be handled uniformly
    by the rest of the system.
    """

    TYPE = "StatisticalTest"
    ICON: str = "Science"

    @abstractmethod
    def run(
        self,
        scores: dict[str, list[float]],  # {run_name: [fold_scores]}
        alpha: float = 0.05,
        **kwargs,
    ) -> StatisticalTestResult:
        """Execute the statistical test on the provided score collections.

        Parameters
        ----------
        scores : dict[str, list[float]]
            Mapping from model or run names to score vectors evaluated over the
            same experimental setup.
        alpha : float, optional
            Significance level used to decide whether the null hypothesis should
            be rejected, by default 0.05.

        Returns
        -------
        StatisticalTestResult
            Result object containing the test statistic, p-value, significance
            decision, and any additional details produced by the implementation.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    @abstractmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Return the metadata used to describe the test in the application.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing UI metadata such as the icon, whether the test
            is parametric or post-hoc, supported alternatives, and the
            interpretation text shown to the user.
        """
        raise NotImplementedError("Subclasses must implement this method")
