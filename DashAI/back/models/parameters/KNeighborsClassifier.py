from typing import Literal

from pydantic import BaseModel, Field


class KNeighborsClassifier(BaseModel):
    n_neighbors: int = Field(
        title="N Neighbors",
        description="""
        The n_neighbors parameter is the number of neighbors
        to consider in each input for classification.
        It must be an integer greater than or equal to 1.""",
        ge=1,
    )
    weights: Literal["uniform", "distance"] = Field(
        title="Weights",
        description="""
        The weights parameter is the weight function used in prediction.
        Possible values: uniform, distance""",
    )
    algorithm: Literal["auto", "ball_tree", "kd_tree", "brute"] = Field(
        title="Algorithm",
        description="""
        The algorithm parameter is the algorithm used to compute the nearest neighbors.
        Possible values: auto, ball_tree, kd_tree, brute""",
    )
