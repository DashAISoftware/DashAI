/* eslint-disable react/prop-types */
import { Box } from "@mui/material";
import React from "react";
import FormSchemaContainer from "./FormSchemaContainer";

function FormSchemaLayout({ children }) {
  return (
    <FormSchemaContainer>
      <Box display="flex" gap={2}>
        <Box flex={1}>{children}</Box>
      </Box>
    </FormSchemaContainer>
  );
}

export default FormSchemaLayout;
