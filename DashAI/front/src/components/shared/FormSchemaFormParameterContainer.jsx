/* eslint-disable react/prop-types */
import React from "react";
import BoxWithTitle from "./BoxWithTitle";
import { Box } from "@mui/material";

function ModelSchemaFormParameterContainer({ children }) {
  return (
    <BoxWithTitle title="Paramenters">
      <Box
        sx={{
          height: 500,
          overflowY: "auto",
          px: 2,
          py: 4,
        }}
      >
        {children}
      </Box>
    </BoxWithTitle>
  );
}

export default ModelSchemaFormParameterContainer;
