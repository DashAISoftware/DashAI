import React from "react";
import BoxWithTitle from "./BoxWithTitle";
import { Box } from "@mui/material";
import PropTypes from "prop-types";

/**
 * This component is a container for the parameters of a model schema
 */

function ModelSchemaParameterContainer({ children }) {
  return (
    <BoxWithTitle title="Paramenters">
      <Box
        sx={{
          px: 2,
          overflowY: "auto",
          py: 4,
          height: 500,
        }}
      >
        {children}
      </Box>
    </BoxWithTitle>
  );
}

ModelSchemaParameterContainer.propTypes = {
  children: PropTypes.node.isRequired,
};

export default ModelSchemaParameterContainer;
