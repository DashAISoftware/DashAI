import React from "react";
import PropTypes from "prop-types";
import FormTooltip from "../FormTooltip";
import { Grid } from "@mui/material";
/**
 * Generic component that wraps each form input
 * @param {string} name name of the input to use as an identifier
 * @param {string} description text to put in a tooltip that helps the user to understand the parameter
 * @param {React.ReactNode} children the input component to render in the layout
 *
 */
function FormInputWrapper({ name, description, children }) {
  return (
    <Grid
      container
      direction="row"
      key={name}
      sx={{ display: "flex", alignItems: "center" }}
      spacing={1}
    >
      {/* Form input */}
      <Grid item xs={11}>
        {children}
      </Grid>

      {/* Tooltip with the parameter description */}
      <Grid item xs={1} sx={{ mb: 2 }}>
        <FormTooltip contentStr={description} />
      </Grid>
    </Grid>
  );
}
FormInputWrapper.propTypes = {
  name: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
};

export default FormInputWrapper;
