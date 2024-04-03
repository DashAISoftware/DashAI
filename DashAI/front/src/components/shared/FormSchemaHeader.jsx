import ArrowBackOutlined from "@mui/icons-material/ArrowBackOutlined";
import { Box, IconButton, Typography } from "@mui/material";
import React from "react";
import { useFormSchemaStore } from "../../contexts/schema";

// eslint-disable-next-line react/prop-types
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

export default FormSchemaHeader;
