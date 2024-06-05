import { Button, ButtonGroup, Typography } from "@mui/material";
import React from "react";

function FormSchemaButtonGroup({
  onCancel,
  onFormSubmit,
  autoSave,
  formik,
  error,
}) {
  return (
    <ButtonGroup size="large" sx={{ justifyContent: "flex-end" }}>
      {onCancel && (
        <Button variant="outlined" onClick={onCancel}>
          Back
        </Button>
      )}
      {!autoSave && (
        <Button
          variant="contained"
          onClick={onFormSubmit}
          disabled={Object.keys(formik?.errors).length > 0 || error}
        >
          Save
        </Button>
      )}
    </ButtonGroup>
  );
}

export default FormSchemaButtonGroup;
