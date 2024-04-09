/* eslint-disable react/prop-types */
import React from "react";
import BoxWithTitle from "./BoxWithTitle";
import { Box } from "@mui/material";

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

export default ModelSchemaParameterContainer;
