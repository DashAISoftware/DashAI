import { Alert, AlertTitle, Box, Link, Stack, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import { Link as RouterLink } from "react-router-dom";

function ExperimentsCreateDatasetStepLayout({ isEmpty, children }) {
  return (
    <Box sx={{ py: 4, px: 6 }}>
      <Stack spacing={2}>
        <Typography variant="subtitle1" component="h3" sx={{ mb: 3 }}>
          Select a dataset for the selected task
        </Typography>
        {isEmpty && (
          <React.Fragment>
            <Alert severity="warning" sx={{ mb: 2 }}>
              <AlertTitle>
                There is no datasets associated to the selected task.
              </AlertTitle>
              Go to{" "}
              <Link component={RouterLink} to="/app/data">
                data tab
              </Link>{" "}
              to upload one first.
            </Alert>
          </React.Fragment>
        )}
        {children}
      </Stack>
    </Box>
  );
}
ExperimentsCreateDatasetStepLayout.propTypes = {
  isEmpty: PropTypes.bool,
  children: PropTypes.element,
};

export default ExperimentsCreateDatasetStepLayout;
