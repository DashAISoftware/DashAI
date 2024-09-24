import React from "react";
import PropTypes from "prop-types";

import { Box } from "@mui/material";

import FormSchema from "../../shared/FormSchema";
import FormSchemaLayout from "../../shared/FormSchemaLayout";

import { useExplorerContext } from "../context";

function StepConfiguration({ disableChanges = false }) {
  const { explorerData, setExplorerConfig } = useExplorerContext();
  const { selectedExplorer, explorerConfig } = explorerData;

  return (
    <Box
      sx={{
        height: "100%",
        width: "100%",
        mt: 2,
        display: "flex",
        justifyContent: "center",
      }}
    >
      {/* schema items */}
      <FormSchemaLayout>
        <FormSchema
          autoSave
          model={selectedExplorer}
          initialValues={explorerConfig}
          onFormSubmit={(values) => {
            if (disableChanges) return;
            setExplorerConfig({ ...explorerConfig, ...values });
          }}
        />
      </FormSchemaLayout>
    </Box>
  );
}

StepConfiguration.propTypes = {};

export default StepConfiguration;
