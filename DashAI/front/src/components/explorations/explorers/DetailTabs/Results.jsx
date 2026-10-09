import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";

import { Box, CircularProgress } from "@mui/material";

import { getExplorerResults } from "../../../../api/explorer";
import {
  artifactToVisualizerData,
  visualizersKeys,
} from "../../../../utils/artifactVisualizerData";
import {
  TabularVisualizer,
  PlotlyJsonVisualizer,
  ImageVisualizer,
} from "../../Visualizations";

/**
 * Results component to render the results of the exploration
 * @param {Object} props
 * @param {Number} props.id The id of the exploration
 * @param {Boolean} props.updateFlag Flag to update the results
 * @param {Function} props.setUpdateFlag Function to set the update flag
 */
function Results({ id, updateFlag = false, setUpdateFlag = () => {} }) {
  const [loading, setLoading] = useState(false);
  const [dataType, setDataType] = useState(null);
  const [data, setData] = useState(null);

  const fetchExplorerResults = async () => {
    setLoading(true);
    getExplorerResults(id)
      .then((artifacts) => {
        const [artifact] = artifacts ?? [];
        if (!artifact?.type) {
          throw new Error("No artifacts in the response");
        }

        const visualizerData = artifactToVisualizerData(artifact);
        setDataType(visualizerData.dataType);
        setData(visualizerData.data);
      })
      .catch((error) => {
        console.error(error);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  // Fetch the results data on mount
  useEffect(() => {
    // Fetch the results data
    if (id) {
      fetchExplorerResults();
    }
  }, [id]);

  // Fetch the results data on update flag
  useEffect(() => {
    if (updateFlag && id) {
      fetchExplorerResults();
      setUpdateFlag(false);
    }
  }, [updateFlag]);

  return (
    <Box
      sx={{
        height: "100%",
        minHeight: "300px",
        width: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {loading && <CircularProgress />}

      {!loading && dataType === visualizersKeys.tabular && (
        <TabularVisualizer
          loading={loading}
          columns={data.columns}
          rows={data.rows}
        />
      )}

      {!loading && dataType === visualizersKeys.plotly_json && (
        <PlotlyJsonVisualizer data={data} />
      )}

      {!loading &&
        (dataType === visualizersKeys.image_base64 ||
          dataType === visualizersKeys.image_url) && (
          <ImageVisualizer data={data} />
        )}
    </Box>
  );
}

Results.propTypes = {
  id: PropTypes.number.isRequired,
  updateFlag: PropTypes.bool,
  setUpdateFlag: PropTypes.func,
};

export default Results;
