import React from "react";
import { Grid } from "@mui/material";
import GlobalExplainersCard from "./GlobalExplanainersCard";

/**
 * GlobalExplainersGrid
 * @returns Grid component for the explainers
 */
export default function GlobalExplainersGrid() {
  // here explainers should be obtained from the back
  const explainers = [
    {
      explainer_name: "PartialDependence",
      id: 1,
      parameters: {
        categorical_features: [
          "blue",
          "dual_sim",
          "four_g",
          "three_g",
          "touch_screen",
          "wifi",
        ],
        grid_resolution: 10,
        lower_percentile: 0,
        upper_percentile: 1,
      },
      status: 2,
      run_id: 1,
      explanation_path: ".DashAI/explanations/explainer_1.json",
      name: "explainer_1",
      created: "2024-02-20T17:08:28.147688",
    },
    {
      explainer_name: "PermutationFeatureImportance",
      id: 4,
      parameters: {
        scoring: "accuracy",
        n_repeats: 10,
        random_state: 1,
        max_samples: 2,
      },
      status: 2,
      run_id: 1,
      explanation_path: ".DashAI/explanations/explainer_4.json",
      name: "explainer_4",
      created: "2024-02-20T17:08:35.174799",
    },
    {
      explainer_name: "KernelShap",
    },
  ];

  return (
    <Grid
      container
      flex={true}
      flexWrap={"nowrap"}
      direction={"row"}
      overflow={"auto"}
      columnGap={2}
    >
      {explainers.map((explainer, i) => (
        <GlobalExplainersCard explainer={explainer} key={i} />
      ))}
    </Grid>
  );
}
