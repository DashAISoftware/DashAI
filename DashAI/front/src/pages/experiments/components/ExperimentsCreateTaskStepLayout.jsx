import { Box, Stack, TextField, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

function ExperimentsCreateTaskStepLayout({ inputProps, children }) {
  const { error, ...rest } = inputProps;

  return (
    <Box sx={{ py: 4, px: 6 }}>
      <Stack spacing={2}>
        <Typography variant="subtitle1" component="h3" sx={{ mb: 3 }}>
          Enter a name and select the task for the new experiment
        </Typography>

        <TextField
          id="experiment-name-input"
          label="Experiment name"
          fullWidth
          autoComplete="off"
          sx={{ mb: 2 }}
          helperText={
            error
              ? "The experiment name must have at least 4 alphanumeric characters."
              : " "
          }
          error={Boolean(error)}
          {...rest}
        />
        {children}
      </Stack>
    </Box>
  );
}

ExperimentsCreateTaskStepLayout.propTypes = {
  inputProps: PropTypes.object,
  children: PropTypes.element,
};

export default ExperimentsCreateTaskStepLayout;
