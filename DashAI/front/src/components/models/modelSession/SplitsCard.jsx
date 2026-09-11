import React from "react";
import PropTypes from "prop-types";
import { Box, Paper, Typography } from "@mui/material";
import { DescriptionBlock } from "../../shared/FormSchemaFieldCard";

/**
 * Splits card shell same Paper/header visual as FormSchemaFieldCard but without
 * the label hiding CSS so Train / Validation / Test TextField labels stay visible.
 */
function SplitsCard({ label, description, errorMessage, children, warning }) {
  return (
    <Paper variant="outlined" sx={{ borderRadius: 2, overflow: "hidden" }}>
      <Box
        sx={{
          px: 8,
          py: 3,
          borderBottom: "1px solid",
          borderColor: "divider",
        }}
      >
        <Typography
          variant="body2"
          fontWeight={600}
          color={
            errorMessage
              ? "error.main"
              : warning
                ? "warning.main"
                : "text.primary"
          }
        >
          {label}
        </Typography>
      </Box>
      <Box sx={{ px: 8, pt: 2, pb: description || errorMessage ? 2 : 4 }}>
        {children}
      </Box>
      {(description || errorMessage || warning) && (
        <Box sx={{ px: 8, pb: 2 }}>
          <DescriptionBlock
            text={errorMessage ?? description}
            isError={Boolean(errorMessage)}
          />
        </Box>
      )}
    </Paper>
  );
}

SplitsCard.propTypes = {
  label: PropTypes.node,
  description: PropTypes.node,
  errorMessage: PropTypes.node,
  children: PropTypes.node,
  warning: PropTypes.bool,
};

export default SplitsCard;
