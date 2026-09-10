import React, { useState, useEffect, useCallback } from "react";
import PropTypes from "prop-types";
import { Box, Typography, TextField, CircularProgress } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { Search as SearchIcon } from "@mui/icons-material";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";

import SideBar from "../threeSectionLayout/panelContainers/SideBar";
import { getComponents } from "../../api/component";
import ModelListItem from "../models/model/ModelListItem";
import InlineReportCreator from "./InlineReportCreator";
import {
  createAndRunReport,
  hasConfigurableParameters,
} from "./createAndRunReport";
import { useModels } from "../models/ModelsContext";

const matchesQuery = (component, query) =>
  (component.display_name || component.name).toLowerCase().includes(query) ||
  (component.metadata?.description || "").toLowerCase().includes(query);

/**
 * Right-side panel shown while the model detail view is on its Reports
 * tab. Lists the reports compatible with the session's task, mirroring the
 * add-explainers sidebar. Clicking one adds it outright, or opens the
 * parameter dialog when the report has something to configure.
 */
export default function ReportsSidebar({ run, session, onCreated }) {
  const theme = useTheme();
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["models", "reports"]);

  const [reports, setReports] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const { reportToCreate, openReportCreator, closeReportCreator } = useModels();

  const taskName = session?.task_name;

  const fetchReports = useCallback(async () => {
    if (!taskName) return;
    try {
      setLoading(true);
      const response = await getComponents({
        selectTypes: ["Report"],
        relatedComponent: taskName,
      });
      setReports(response);
    } catch (error) {
      console.error("Error fetching reports:", error);
      enqueueSnackbar(t("reports:error.fetch"), { variant: "error" });
    } finally {
      setLoading(false);
    }
  }, [taskName, enqueueSnackbar, t]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  // A report with nothing to configure is added on the click. Opening a
  // dialog whose only control is a Create button would be pure friction.
  const handleSelect = async (report) => {
    if (hasConfigurableParameters(report)) {
      openReportCreator(report);
      return;
    }
    try {
      await createAndRunReport({
        runId: run.id,
        reportName: report.name,
        t,
        enqueueSnackbar,
        onCreated,
      });
    } catch (error) {
      console.error("Error creating report:", error);
      enqueueSnackbar(t("reports:error.create"), { variant: "error" });
    }
  };

  const query = searchQuery.trim().toLowerCase();
  const filtered = query
    ? reports.filter((item) => matchesQuery(item, query))
    : reports;

  return (
    <SideBar>
      <Box
        sx={{
          p: 4,
          borderBottom: `1px solid ${theme.palette.ui.border}`,
          flexShrink: 0,
          display: "flex",
          alignItems: "center",
          height: 64,
        }}
      >
        <Typography variant="h6" color="text.primary">
          {t("reports:label.availableReports")}
        </Typography>
      </Box>

      <Box sx={{ p: 4, flexShrink: 0 }}>
        <TextField
          fullWidth
          size="small"
          placeholder={t("reports:label.searchReports")}
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
          slotProps={{
            input: {
              startAdornment: (
                <SearchIcon sx={{ mr: 2, color: "text.secondary" }} />
              ),
            },
          }}
        />
      </Box>

      <Box sx={{ flex: 1, overflowY: "auto", px: 4, pb: 4 }}>
        {loading ? (
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              height: "100%",
            }}
          >
            <CircularProgress size={32} />
          </Box>
        ) : filtered.length === 0 ? (
          <Typography
            variant="body2"
            sx={{ color: "text.secondary", textAlign: "center", py: 2 }}
          >
            {searchQuery
              ? t("reports:label.noReportsMatchSearch")
              : t("reports:label.noCompatibleReportsFound")}
          </Typography>
        ) : (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
            {filtered.map((report) => (
              <ModelListItem
                key={report.name}
                model={report}
                draggable
                dragType="application/x-dashai-report"
                dragPayload={{
                  name: report.name,
                  display_name: report.display_name,
                  // Lets the drop target decide between adding the report
                  // outright and opening the parameter dialog, exactly as
                  // handleSelect does for a click.
                  schema: report.schema,
                }}
                onClick={() => handleSelect(report)}
              />
            ))}
          </Box>
        )}
      </Box>

      {reportToCreate && (
        <InlineReportCreator
          open
          runId={run.id}
          reportName={reportToCreate.name}
          displayName={reportToCreate.display_name}
          onCreated={onCreated}
          onCancel={closeReportCreator}
        />
      )}
    </SideBar>
  );
}

ReportsSidebar.propTypes = {
  run: PropTypes.shape({
    id: PropTypes.number.isRequired,
  }).isRequired,
  session: PropTypes.shape({
    task_name: PropTypes.string,
  }),
  onCreated: PropTypes.func,
};
