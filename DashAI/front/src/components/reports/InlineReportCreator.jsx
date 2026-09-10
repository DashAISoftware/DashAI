import React, { useEffect, useMemo, useRef, useState } from "react";
import PropTypes from "prop-types";
import {
  Box,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Typography,
} from "@mui/material";
import { Close as CloseIcon } from "@mui/icons-material";
import { LoadingButton } from "@mui/lab";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";

import useSchema from "../../hooks/useSchema";
import ConfigureReportStep from "./ConfigureReportStep";
import { createAndRunReport } from "./createAndRunReport";

const SNACKBAR_AUTO_HIDE_MS = 5000;

/**
 * Creation dialog for one evaluation report.
 *
 * A report covers every evaluation partition of the run, so there is nothing
 * left to choose but its parameters, and most reports have none. What remains
 * is a single confirm rather than a wizard.
 */
export default function InlineReportCreator({
  open,
  runId,
  reportName,
  displayName,
  onCreated,
  onCancel,
}) {
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["reports", "common"]);
  const formSubmitRef = useRef(null);

  const { defaultValues, loading: schemaLoading } = useSchema({
    modelName: reportName,
  });
  const hasParameters =
    Boolean(defaultValues) && Object.keys(defaultValues).length > 0;

  const defaultNewReport = useMemo(
    () => ({ run_id: runId, report_name: reportName, parameters: null }),
    [runId, reportName],
  );

  const [newReport, setNewReport] = useState(defaultNewReport);
  const [valid, setValid] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!open) {
      setNewReport(defaultNewReport);
      setValid(true);
    }
  }, [open, defaultNewReport]);

  const handleCreate = async () => {
    setIsLoading(true);
    try {
      await createAndRunReport({
        runId: newReport.run_id,
        reportName: newReport.report_name,
        parameters: newReport.parameters ?? {},
        t,
        enqueueSnackbar,
        onCreated,
      });
      onCancel();
    } catch (error) {
      enqueueSnackbar(t("reports:error.create"), {
        variant: "error",
        autoHideDuration: SNACKBAR_AUTO_HIDE_MS,
      });
      console.error("Error details:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onCancel} maxWidth="md" fullWidth>
      <DialogTitle sx={{ bgcolor: "background.paper" }}>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Typography variant="h6" component="span">
            {t("reports:label.newReport")}
            {`: ${displayName || reportName}`}
          </Typography>
          <IconButton
            onClick={onCancel}
            size="small"
            sx={{ color: "text.secondary" }}
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers sx={{ bgcolor: "background.paper" }}>
        {hasParameters ? (
          <ConfigureReportStep
            newReport={newReport}
            setNewReport={setNewReport}
            setNextEnabled={setValid}
            formSubmitRef={formSubmitRef}
            defaultValues={defaultValues}
          />
        ) : (
          <Typography variant="body2" color="text.secondary">
            {t("reports:message.coversEveryPartition")}
          </Typography>
        )}
      </DialogContent>

      <DialogActions sx={{ p: 2, bgcolor: "background.paper" }}>
        <LoadingButton
          onClick={handleCreate}
          variant="contained"
          color="primary"
          disabled={!valid || isLoading || schemaLoading}
          loading={isLoading}
        >
          {t("reports:button.create")}
        </LoadingButton>
      </DialogActions>
    </Dialog>
  );
}

InlineReportCreator.propTypes = {
  open: PropTypes.bool.isRequired,
  runId: PropTypes.number.isRequired,
  reportName: PropTypes.string.isRequired,
  displayName: PropTypes.string,
  onCreated: PropTypes.func,
  onCancel: PropTypes.func.isRequired,
};
