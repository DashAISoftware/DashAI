import React, { useState, useEffect } from "react";
import {
  TabularVisualizer,
  PlotlyJsonVisualizer,
  ImageVisualizer,
} from "../../explorations/Visualizations";
import { Box, Typography } from "@mui/material";
import { getExplorationResults } from "../../../api/pipeline";
import {
  artifactToVisualizerData,
  visualizersKeys,
} from "../../../utils/artifactVisualizerData";

function Results({ pipelineId }) {
  const [explorationResults, setExplorationResults] = useState(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const response = await getExplorationResults(pipelineId);
        setExplorationResults(response);
      } catch (error) {
        console.error("Error fetching results:", error);
      }
    };

    if (pipelineId) {
      fetchResults();
    }
  }, [pipelineId]);

  const renderArtifact = (artifact, key) => {
    let visualizerData;
    try {
      visualizerData = artifactToVisualizerData(artifact);
    } catch (error) {
      console.error(error);
      return null;
    }
    const { dataType, data } = visualizerData;

    if (dataType === visualizersKeys.tabular) {
      return (
        <TabularVisualizer key={key} columns={data.columns} rows={data.rows} />
      );
    }

    if (dataType === visualizersKeys.plotly_json) {
      return <PlotlyJsonVisualizer key={key} data={data} />;
    }

    if (
      dataType === visualizersKeys.image_base64 ||
      dataType === visualizersKeys.image_url
    ) {
      return <ImageVisualizer key={key} data={data} />;
    }

    return null;
  };

  if (!explorationResults) {
    return <Typography variant="body2">Loading...</Typography>;
  }

  return (
    <Box
      sx={{
        width: "100%",
        display: "flex",
        flexDirection: "column",
        gap: 4,
        padding: 4,
      }}
    >
      {Object.entries(explorationResults).map(
        ([explorationName, result], i) => (
          <Box key={explorationName} sx={{ width: "100%", minWidth: "800px" }}>
            <Typography gutterBottom variant="h6" color={"GrayText"}>
              {i}: {result.exploration_type}
              {result.name ? ` | ${result.name}` : ""}
            </Typography>
            {(result.results ?? []).map((artifact, artifactIndex) =>
              renderArtifact(artifact, `${explorationName}-${artifactIndex}`),
            )}
          </Box>
        ),
      )}
    </Box>
  );
}

export default Results;
