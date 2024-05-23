import React from "react";
import BoxWithTitle from "./BoxWithTitle";
import { Box } from "@mui/material";
import PropTypes from "prop-types";

/**
 * This component is a container for the parameters of a model schema
 */

function FormSchemaParameterContainer({ children }) {
  return (
    <BoxWithTitle title="Parameters">
      <Box
        sx={{
          px: 2,
          overflowY: "auto",
          py: 4,
          height: "auto",
          width: "inherit",
        }}
      >
        {children}
      </Box>
    </BoxWithTitle>
  );
}

FormSchemaParameterContainer.propTypes = {
  children: PropTypes.node.isRequired,
};

export default FormSchemaParameterContainer;
