"""Base Optimizer abstract class."""

import logging
from abc import ABCMeta, abstractmethod
from typing import Final

from DashAI.back.config_object import ConfigObject
from DashAI.back.core.artifacts import PlotlyArtifact

log = logging.getLogger(__name__)


class BaseOptimizer(ConfigObject, metaclass=ABCMeta):
    """
    Abstract class of all hyperparameter's Optimizers.

    All models must extend this class and implement optimize method.
    """

    TYPE: Final[str] = "Optimizer"

    @abstractmethod
    def optimize(self, model, input, output, parameters, metric, strategy):
        """
        Run hyperparameter optimization.

        Parameters
        ----------
        model : object
            Model instance to optimize.
        input_dataset : dict
            Dataset splits keyed by "train" and "validation".
        output_dataset : dict
            Label splits keyed by "train" and "validation".
        parameters : list
            Tuples of (obj, key, bounds, dtype) for each hyperparameter.
        metric : dict
            Dict with keys "class" (metric instance) and "metadata".
        strategy : callable
            Function that trains the model and returns a score based on the metric.
            Depends on the specific evaluation strategy used.
        """
        raise NotImplementedError(
            "Optimization modules must implement optimize method."
        )

    @abstractmethod
    def get_model(self):
        """
        Get the model with the best set of hyperparameters found

        Returns
        -------
            best_model (object): Object from the class model with
                                    the best hyperparameters found.
        """
        raise NotImplementedError(
            "Optimization modules must implement get_model method."
        )

    @abstractmethod
    def get_trials_values(self):
        """
        Get the trial values from the hyperparameter optimization process

        Returns
        -------
            trial_values (list): List with the hyperparameters
                                    values and the goal metric per trial.
        """
        raise NotImplementedError(
            "Optimization modules must implement get_trials_values method."
        )

    @abstractmethod
    def get_best_params(self):
        """
        Get the best hyperparameters found during optimization

        Returns
        -------
            best_params (dict): Dictionary with the best hyperparameters found.
        """
        raise NotImplementedError(
            "Optimization modules must implement get_best_params method."
        )

    def history_objective_plot(self, trials, goal_metric):
        """
        Plot for the goal metric achieved per trial.

        Args:
            trial_values (list): List with the hyperparameters values
                                    and the goal metric per trial.

        Returns
        -------
            artifact (PlotlyArtifact): typed artifact wrapping the plot data
        """
        # Lazy imports
        import numpy as np
        import plotly.graph_objects as go

        x = list(range(1, len(trials) + 1))
        y = [trial["value"] for trial in trials]
        cumulative = (
            np.maximum.accumulate(y)
            if goal_metric["metadata"]["maximize"]
            else np.minimum.accumulate(y)
        )
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="markers",
                name="Optimization History",
                marker_color="blue",
                marker_size=8,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=x,
                y=cumulative,
                mode="lines",
                name=(
                    "Current Max Value"
                    if goal_metric["metadata"]["maximize"]
                    else "Current Min Value"
                ),
                line_color="red",
                line_width=2,
            )
        )
        title = (
            "Optimization History with Current Max Value"
            if goal_metric["metadata"]["maximize"]
            else "Optimization History with Current Min Value"
        )
        fig.update_layout(
            title=title,
            xaxis_title="Trial",
            yaxis_title=goal_metric["name"],
        )
        return PlotlyArtifact(payload=fig, title=title)

    def slice_plot(self, trials, goal_metric):
        """
        Plot that compares the performance in the
        search space of one hyperparameter.

        Args:
            trial_values (list): List with the hyperparameters
                            values and the goal metric per trial.

        Returns
        -------
            artifact (PlotlyArtifact): typed artifact wrapping the plot data
        """
        # Lazy imports
        import plotly.graph_objects as go

        param_names = list(trials[0]["params"].keys())

        traces = []
        for param_name in param_names:
            x_values = [trial["params"][param_name] for trial in trials]
            y_values = [trial["value"] for trial in trials]
            trial_numbers = list(range(1, len(trials) + 1))

            trace = go.Scatter(
                x=x_values,
                y=y_values,
                mode="markers",
                marker={
                    "size": 8,
                    "color": trial_numbers,
                    "colorscale": "Blues",
                    "colorbar": {"title": "Trial Number"},
                    "showscale": True,
                    "line": {"width": 0.2, "color": "black"},
                },
                name=param_name,
                visible=False,
            )
            traces.append(trace)

        traces[0]["visible"] = True

        buttons = []
        for i, param_name in enumerate(param_names):
            buttons.append(
                {
                    "method": "update",
                    "label": param_name,
                    "args": [
                        {"visible": [j == i for j in range(len(param_names))]},
                        {
                            "title": f"Slice plot for {param_name}",
                            "xaxis": {"title": param_name},
                        },
                    ],
                }
            )

        updatemenus = [{"buttons": buttons, "direction": "down", "showactive": True}]

        title = f"Slice plot for {param_names[0]}"
        fig = go.Figure(data=traces)
        fig.update_layout(
            updatemenus=updatemenus,
            title=title,
            xaxis_title=param_names[0],
            yaxis_title=goal_metric["name"],
        )

        return PlotlyArtifact(payload=fig, title=title)

    def contour_plot(self, trials, goal_metric):
        """
        Contour plot between two hyperparameters
        and the goal metric achieved in the search space.

        Args:
            trial_values (list): List with the hyperparameters values
                                and the goal metric per trial.

        Returns
        -------
            artifact (PlotlyArtifact): typed artifact wrapping the plot data
        """
        # Lazy imports
        import plotly.graph_objects as go

        param_names = list(trials[0]["params"].keys())
        traces = []
        scatter_traces = []
        for param_x in param_names:
            for param_y in param_names:
                if param_x != param_y:
                    x_values = [
                        trial["params"][param_x]
                        for trial in trials
                        if param_x in trial["params"]
                    ]
                    y_values = [
                        trial["params"][param_y]
                        for trial in trials
                        if param_y in trial["params"]
                    ]
                    z_values = [
                        trial["value"]
                        for trial in trials
                        if param_x in trial["params"] and param_y in trial["params"]
                    ]

                    contour_trace = go.Contour(
                        x=x_values,
                        y=y_values,
                        z=z_values,
                        colorscale="Blues",
                        colorbar={"title": goal_metric["name"]},
                        showscale=True,
                        name=f"{param_x} vs {param_y}",
                        visible=False,
                    )
                    traces.append(contour_trace)

                    scatter_trace = go.Scatter(
                        x=x_values,
                        y=y_values,
                        mode="markers",
                        marker={
                            "size": 8,
                            "color": z_values,
                            "colorscale": "Blues",
                            "colorbar": {"title": goal_metric["name"]},
                            "showscale": False,
                            "line": {"width": 0.2, "color": "black"},
                        },
                        name=f"{param_x} vs {param_y} points",
                        visible=False,
                    )
                    scatter_traces.append(scatter_trace)

        traces[0]["visible"] = True
        scatter_traces[0]["visible"] = True

        buttons = []
        for i in range(len(traces)):
            buttons.append(
                {
                    "method": "update",
                    "label": traces[i]["name"],
                    "args": [
                        {
                            "visible": [j == i for j in range(len(traces))]
                            + [j == i for j in range(len(scatter_traces))]
                        },
                        {"title": f"Contour plot for {traces[i]['name']}"},
                    ],
                }
            )

        updatemenus = [{"buttons": buttons, "direction": "down", "showactive": True}]

        title = f"Contour plot for {traces[0]['name']}"
        fig = go.Figure(data=traces + scatter_traces)
        fig.update_layout(
            updatemenus=updatemenus,
            title=title,
            xaxis_title=param_names[0],
            yaxis_title=param_names[1],
        )
        return PlotlyArtifact(payload=fig, title=title)

    def importance_plot(self, trials, goal_metric):
        """
        Plot to obtain the importance between all the hyperparameters
        involved in hyperparameter optimization.

        Args:
            trial_values (list): List with the hyperparameters values
                                and the goal metric per trial.

        Returns
        -------
            artifact (PlotlyArtifact): typed artifact wrapping the plot data
        """
        # Lazy imports
        import optuna
        import plotly.graph_objects as go
        from optuna.importance import FanovaImportanceEvaluator

        distributions = {}
        for _, param, (low, high), dtype in self.parameters:
            if dtype == "integer":
                distributions[param] = optuna.distributions.IntDistribution(low, high)
            elif dtype == "number":
                distributions[param] = optuna.distributions.FloatDistribution(low, high)

        direction = "maximize" if goal_metric["metadata"]["maximize"] else "minimize"
        study = optuna.create_study(direction=direction)
        for trial in trials:
            study.add_trial(
                optuna.trial.create_trial(
                    params=trial["params"],
                    distributions=distributions,
                    value=trial["value"],
                    state=optuna.trial.TrialState.COMPLETE,
                )
            )
        try:
            evaluator = FanovaImportanceEvaluator()
            importances = evaluator.evaluate(study)
        except RuntimeError:
            importances = {
                param: 1.0 / len(self.parameters) for _, param, _, _ in self.parameters
            }
            log.warning(
                "Could not calculate parameter importance using FANOVA. "
                "Using equal importances."
            )

        sorted_items = sorted(importances.items(), key=lambda item: item[1])
        param_names, importance_values = zip(*sorted_items, strict=False)
        fig = go.Figure(
            data=[
                go.Bar(
                    x=importance_values,
                    y=param_names,
                    orientation="h",
                    text=importance_values,
                    textposition="outside",
                    texttemplate="%{text:.2f}",
                )
            ]
        )

        title = "Hyperparameter importance"
        fig.update_layout(
            title=title,
            xaxis_title="Importance",
            yaxis_title="Hyperparameter",
            yaxis={"tickangle": 0},
        )

        return PlotlyArtifact(payload=fig, title=title)

    def create_plots(self, trials, run_id, n_params, goal_metric):
        """
        List of available plots.

        Args:
            trials (list): List with the hyperparameters values
                            and the goal metric per trial.
            run_id (int): Number with the id associated to the current run
                            from the experiment.
            n_params (int): Number of the different hyperparameters involved
                            in the process of hyperparameter optimization
            goal_metric (dict): Metric optimized in the process.

        Returns
        -------
            plots_filenames (list): Filenames to persist each plot under.
            plots_list (list): The matching list of PlotlyArtifact instances.
        """
        if n_params >= 2:
            plots_filenames = [
                f"history_objective_plot_{run_id}.pickle",
                f"slice_plot_{run_id}.pickle",
                f"contour_plot_{run_id}.pickle",
                f"importance_plot_{run_id}.pickle",
            ]
            plots_list = [
                self.history_objective_plot(trials, goal_metric),
                self.slice_plot(trials, goal_metric),
                self.contour_plot(trials, goal_metric),
                self.importance_plot(trials, goal_metric),
            ]
            return plots_filenames, plots_list
        else:
            plots_filenames = [
                f"history_objective_plot_{run_id}.pickle",
                f"slice_plot_{run_id}.pickle",
            ]
            plots_list = [
                self.history_objective_plot(trials, goal_metric),
                self.slice_plot(trials, goal_metric),
            ]
            return plots_filenames, plots_list
