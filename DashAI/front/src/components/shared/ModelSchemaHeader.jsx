import ArrowBackOutlined from "@mui/icons-material/ArrowBackOutlined";
import { Box, IconButton, Typography } from "@mui/material";
import React from "react";
import { useModelSchemaStore } from "../../contexts/schema";

// eslint-disable-next-line react/prop-types
function ModelSchemaHeader({ title, onClose }) {
  const { properties, removeLastProperty } = useModelSchemaStore();

  const handleClose = () => {
    if (properties.length > 0) {
      removeLastProperty();
    } else {
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

export default ModelSchemaHeader;
