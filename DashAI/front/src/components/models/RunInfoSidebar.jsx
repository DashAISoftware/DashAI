import React, { useState } from "react";
import PropTypes from "prop-types";
import { Box, Typography, Tabs, Tab } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import SideBar from "../threeSectionLayout/panelContainers/SideBar";
import ModelConfigurationContent from "./ModelConfigurationContent";
import SessionInfoContent from "./SessionInfoContent";
import ParamInfoList from "./ParamInfoBox";

function formatCreatedDate(dateStr, locale) {
  if (!dateStr) return null;
  const date = new Date(dateStr);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleString(locale, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDuration(startTime, endTime) {
  if (!startTime || !endTime) return null;
  const totalSeconds = Math.max(
    0,
    Math.round((new Date(endTime) - new Date(startTime)) / 1000),
  );
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return minutes > 0
    ? `${minutes}m ${String(seconds).padStart(2, "0")}s`
    : `${seconds}s`;
}

/**
 * Right-side panel shown while inside a run's full-screen model detail
 * view. Two tabs, same pattern as the notebook Explore/Convert sidebar:
 * "Run" (the run's quick facts and trained configuration — what the "Run
 * Information" modal used to show) and "Session" (the parent session's
 * setup, same content as InfoSessionModal), both always visible inline
 * instead of behind a separate button.
 */
export default function RunInfoSidebar({
  run,
  model,
  datasetName,
  session,
  datasets,
  tasks,
}) {
  const theme = useTheme();
  const { t, i18n } = useTranslation(["models", "common"]);
  const [activeTab, setActiveTab] = useState(0);

  const modelDisplayName = model?.display_name || run.model_name;
  const createdLabel = formatCreatedDate(run.created, i18n.language);
  const durationLabel = formatDuration(run.start_time, run.end_time);

  const rows = [
    [t("common:id"), run.id],
    [t("common:model"), modelDisplayName],
    [t("common:associatedDataset"), datasetName || t("common:unknown")],
    [t("common:createdAt"), createdLabel || t("common:unknown")],
    [t("common:duration"), durationLabel || t("common:unknown")],
  ];

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
          {t("models:label.configuration")}
        </Typography>
      </Box>

      <Tabs
        value={activeTab}
        onChange={(_event, newValue) => setActiveTab(newValue)}
        centered
        sx={{
          flexShrink: 0,
          borderBottom: `1px solid ${theme.palette.ui.border}`,
        }}
      >
        <Tab label={t("common:model")} />
        <Tab label={t("common:session")} />
      </Tabs>

      <Box sx={{ flex: 1, overflowY: "auto", p: 4 }}>
        {activeTab === 0 ? (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <ModelConfigurationContent run={run} model={model} />

            <Box>
              <Typography variant="subtitle2" gutterBottom>
                {t("common:metadata")}
              </Typography>
              <ParamInfoList rows={rows} />
            </Box>
          </Box>
        ) : (
          <SessionInfoContent
            session={session}
            datasets={datasets}
            tasks={tasks}
          />
        )}
      </Box>
    </SideBar>
  );
}

RunInfoSidebar.propTypes = {
  run: PropTypes.shape({
    id: PropTypes.number,
    model_name: PropTypes.string,
    created: PropTypes.string,
    start_time: PropTypes.string,
    end_time: PropTypes.string,
    parameters: PropTypes.object,
    optimizer_name: PropTypes.string,
    optimizer_parameters: PropTypes.object,
    goal_metric: PropTypes.string,
  }).isRequired,
  model: PropTypes.shape({
    display_name: PropTypes.string,
    schema: PropTypes.object,
  }),
  datasetName: PropTypes.string,
  session: PropTypes.shape({
    id: PropTypes.number,
    name: PropTypes.string,
    dataset_id: PropTypes.number,
    task_name: PropTypes.string,
    input_columns: PropTypes.array,
    output_columns: PropTypes.array,
    splits: PropTypes.oneOfType([PropTypes.string, PropTypes.object]),
    created: PropTypes.string,
    last_modified: PropTypes.string,
    description: PropTypes.string,
  }),
  datasets: PropTypes.array,
  tasks: PropTypes.array,
};
