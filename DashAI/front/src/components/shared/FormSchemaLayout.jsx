import { Box } from "@mui/material";
import React from "react";
import FormSchemaContainer from "./FormSchemaContainer";
import PropTypes from "prop-types";

/**
 * Layout for the form schema when it is not in a dialog
 */

function FormSchemaLayout({ children }) {
  return (
    <FormSchemaContainer>
      <Box display="flex" gap={2}>
        <Box flex={1}>{children}</Box>
      </Box>
    </FormSchemaContainer>
  );
}

FormSchemaLayout.propTypes = {
  children: PropTypes.node.isRequired,
};

export default FormSchemaLayout;
