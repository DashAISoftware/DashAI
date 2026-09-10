import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import FormSchema from "../shared/FormSchema";
import FormSchemaLayout from "../shared/FormSchemaLayout";

/**
 * Parameter step of the report creator, rendered from the component's own
 * schema the same way every other configurable object in DashAI is configured.
 *
 * Only reached for reports that actually take parameters; the creator
 * drops this step entirely for the ones that do not.
 */
export default function ConfigureReportStep({
  newReport,
  setNewReport,
  setNextEnabled,
  formSubmitRef,
  defaultValues,
}) {
  const { t } = useTranslation(["reports"]);
  const [error, setError] = useState(false);

  const isParamsEmpty =
    !newReport.parameters || Object.keys(newReport.parameters).length === 0;

  useEffect(() => {
    if (isParamsEmpty && Boolean(defaultValues)) {
      setNewReport((prev) => ({ ...prev, parameters: defaultValues }));
    }
  }, [isParamsEmpty, defaultValues, setNewReport]);

  useEffect(() => {
    setNextEnabled(!error);
  }, [error, setNextEnabled]);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <Typography variant="subtitle2">
        {t("reports:label.parameters")}
      </Typography>
      <FormSchemaLayout>
        <FormSchema
          autoSave
          model={newReport.report_name}
          onFormSubmit={(values) =>
            setNewReport((prev) => ({ ...prev, parameters: values }))
          }
          setError={setError}
          formSubmitRef={formSubmitRef}
        />
      </FormSchemaLayout>
    </Box>
  );
}

ConfigureReportStep.propTypes = {
  newReport: PropTypes.shape({
    report_name: PropTypes.string,
    parameters: PropTypes.object,
  }).isRequired,
  setNewReport: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
  formSubmitRef: PropTypes.shape({ current: PropTypes.any }).isRequired,
  defaultValues: PropTypes.object,
};
