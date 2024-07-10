import ArrowBackOutlined from "@mui/icons-material/ArrowBackOutlined";
import { Box, IconButton, Typography } from "@mui/material";
import React from "react";
import { useFormSchemaStore } from "../../contexts/schema";
import PropTypes from "prop-types";

/**
 * This component is the header for the form schema when parent model is selected.
 * @param {string} title - The title of the form schema
 * @param {function} onClose - The function to close the form schema
 * @param {function} onFormSubmit - The function to submit the form
 */

function FormSchemaHeader({ title, onClose, onFormSubmit }) {
  const { formValues, properties, removeLastProperty } = useFormSchemaStore();

  const handleClose = () => {
    if (properties.length > 0) {
      removeLastProperty();
    } else {
      onFormSubmit(formValues);
      onClose();
    }
  };

  return (
    <Box display="flex" alignItems="center">
      <IconButton onClick={handleClose}>
        <ArrowBackOutlined />
      </IconButton>
      <Typography variant="h5" sx={{ ml: 2 }}>
        {title}
      </Typography>
    </Box>
  );
}

FormSchemaHeader.propTypes = {
  title: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
  onFormSubmit: PropTypes.func.isRequired,
};

export default FormSchemaHeader;
