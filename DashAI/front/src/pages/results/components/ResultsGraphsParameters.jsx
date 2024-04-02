import React from "react";
import PropTypes from "prop-types";
import { Radio, RadioGroup, FormControlLabel, Box, Checkbox } from "@mui/material";

function ResultsGraphsParameters({ showCustomMetrics, tabularMetrics, selectedParameters,
                               handleToggleParameter, selectedGeneralMetric, setSelectedGeneralMetric,
                               setSelectedParameters, concatenatedMetrics }) {
  return (
    <Box
        bgcolor="#2F2F2F"
        p={2}
        mr={1}
        display="flex"
        flexDirection="column"
        alignItems="flex-start"
        width="250px"
        sx={{
        "& .MuiCheckbox-root": {
            padding: "3px 0",
        },
        "& .MuiTypography-root": {
            padding: "3px 0",
        },
        }}
    >
        {showCustomMetrics
        ? tabularMetrics.map((param) => (
            <FormControlLabel
                key={param}
                control={<Checkbox checked={selectedParameters.includes(param)} onChange={() => handleToggleParameter(param)} />}
                label={param}
            />
            ))
        : (
        <RadioGroup 
            value={selectedGeneralMetric} 
            onChange={(event) => {
            const selectedMetric = event.target.value;
            setSelectedGeneralMetric(selectedMetric);
            setSelectedParameters([selectedMetric]);
            }}
        >
            {concatenatedMetrics.map((param) => (
            <FormControlLabel
                key={param}
                value={param}
                control={<Radio checked={selectedGeneralMetric === param} />}
                label={param}
            />
            ))}
        </RadioGroup>
        )
        }   
    </Box>
  );
}

ResultsGraphsParameters.propTypes = {
    showCustomMetrics: PropTypes.bool.isRequired,
    handleToggleMetrics: PropTypes.func,
    selectedParameters: PropTypes.array.isRequired,
    handleToggleParameter: PropTypes.func.isRequired,
    selectedGeneralMetric: PropTypes.string.isRequired,
    setSelectedGeneralMetric: PropTypes.func.isRequired,
    setSelectedParameters: PropTypes.func.isRequired,
    concatenatedMetrics: PropTypes.array.isRequired,
  };

export default ResultsGraphsParameters;
