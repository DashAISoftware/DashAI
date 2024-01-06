import { Box, Paper } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

function ExperimentsTableLayout({ toolbar, children }) {
  return (
    <Paper sx={{ py: 4, px: 6 }}>
      <Box display="flex" flexDirection="column">
        {toolbar}
        <Box py={4}>{children}</Box>
      </Box>
    </Paper>
  );
}

ExperimentsTableLayout.propTypes = {
  toolbar: PropTypes.element,
  children: PropTypes.element,
};

export default ExperimentsTableLayout;
