import { Box, IconButton, Typography } from "@mui/material";
import React from "react";

import ModeEditIcon from "@mui/icons-material/ModeEdit";
import { useModelSchemaStore } from "../../contexts/schema";
import FormTooltip from "../configurableObject/FormTooltip";

// eslint-disable-next-line react/prop-types
function ModelSchemaSubform({ name, label, description }) {
  const { addProperty } = useModelSchemaStore();

  return (
    <Box
      key={name}
      display="flex"
      sx={{ width: "100%", pb: 2 }}
      alignItems="center"
      justifyContent={"space-between"}
    >
      {/* Dropdown to select a configurable object to render a subform */}
      <Box flex={1} sx={{ whiteSpace: "nowrap" }}>
        <Typography>{label}</Typography>
      </Box>
      <Box display="flex">
        <IconButton
          color="primary"
          component="label"
          onClick={() => addProperty({ key: name, label })}
        >
          <ModeEditIcon />
        </IconButton>
        <FormTooltip contentStr={description} />
      </Box>
    </Box>
  );
}

export default ModelSchemaSubform;
