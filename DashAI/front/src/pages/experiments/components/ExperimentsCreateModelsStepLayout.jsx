import { Box, Stack, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

function ExperimentsCreateModelsStepLayout({ toolbar, children }) {
  return (
    <Box sx={{ py: 4, px: 6 }}>
      <Stack spacing={2}>
        <Typography variant="subtitle1" component="h3" sx={{ mb: 3 }}>
          Add models to your experiment
        </Typography>
        {toolbar}
        {children}
      </Stack>
    </Box>
  );
}
ExperimentsCreateModelsStepLayout.propTypes = {
  toolbar: PropTypes.element,
  children: PropTypes.element,
};

export default ExperimentsCreateModelsStepLayout;
