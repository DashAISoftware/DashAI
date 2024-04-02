import React from "react";
import PropTypes from "prop-types";
import { Box, Button } from "@mui/material";

function ResultsGraphsSelection({ selectedChart, handleChangeChart }) {
  return (
    <Box p={2} mb={2}>
      <Button
        variant="text"
        color={selectedChart === "radar" ? "primary" : "inherit"}
        onClick={() => handleChangeChart("radar")}
        style={{
          borderBottom:
            selectedChart === "radar"
              ? "2px solid #00bebb"
              : "2px solid #ffffff",
          marginRight: "30px",
          marginTop: "-15px",
        }}
      >
        Radar
      </Button>
      <Button
        variant="text"
        color={selectedChart === "bar" ? "primary" : "inherit"}
        onClick={() => handleChangeChart("bar")}
        style={{
          borderBottom:
            selectedChart === "bar" ? "2px solid #00bebb" : "2px solid #ffffff",
          marginTop: "-15px",
        }}
      >
        Bar
      </Button>
      <Button
        variant="text"
        color={selectedChart === "pie" ? "primary" : "inherit"}
        onClick={() => handleChangeChart("pie")}
        style={{
          borderBottom:
            selectedChart === "pie" ? "2px solid #00bebb" : "2px solid #ffffff",
          marginLeft: "30px",
          marginTop: "-15px",
        }}
      >
        Pie
      </Button>
    </Box>
  );
}

ResultsGraphsSelection.propTypes = {
  selectedChart: PropTypes.string.isRequired,
  handleChangeChart: PropTypes.func.isRequired,
};

export default ResultsGraphsSelection;
