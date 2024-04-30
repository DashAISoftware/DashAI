/* eslint-disable react/prop-types */
import { Box, Collapse, IconButton, Typography } from "@mui/material";
import React from "react";

import ModeEditIcon from "@mui/icons-material/ModeEdit";
import { useFormSchemaStore } from "../../contexts/schema";
import FormTooltip from "../configurableObject/FormTooltip";

// eslint-disable-next-line react/prop-types
function FormSchemaSubform({
  name,
  label,
  description,
  errorMessage,
  children,
}) {
  const { addProperty } = useFormSchemaStore();
  const [showSection, setShowSection] = React.useState(false);

  const handleClick = () => {
    if (!children) {
      addProperty({ key: name, label });
    } else {
      setShowSection(!showSection);
    }
  };

  return (
    <>
      <Box
        key={name}
        display="flex"
        sx={{ width: "100%", pb: 2 }}
        alignItems="center"
        justifyContent={"space-between"}
      >
        <Box
          flex={1}
          sx={{
            whiteSpace: "nowrap",
            color: errorMessage ? "error.main" : null,
          }}
        >
          <Typography>{label}</Typography>
        </Box>
        <Box display="flex">
          <IconButton
            color={errorMessage ? "error" : "primary"}
            component="label"
            onClick={handleClick}
          >
            <ModeEditIcon />
          </IconButton>
          <FormTooltip
            contentStr={errorMessage ?? description}
            error={Boolean(errorMessage)}
          />
        </Box>
      </Box>
      <Collapse in={showSection}>{children}</Collapse>
    </>
  );
}

export default FormSchemaSubform;
