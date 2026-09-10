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
import InlineExplainerCreator from "./InlineExplainerCreator";
import { useModels } from "../models/ModelsContext";

const matchesQuery = (component, query) =>
  (component.display_name || component.name).toLowerCase().includes(query) ||
  (component.metadata?.description || "").toLowerCase().includes(query);

/**
 * Right-side panel shown while the model detail view is on its Explainers
 * tab. Lists the global/local explainers compatible with the session's task
 * (mirroring the add-models sidebar); clicking one opens the explainer
 * creation stepper with that explainer preselected.
 */
export default function ExplainersSidebar({ run, session, onCreated }) {
  const theme = useTheme();
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["models", "explainers"]);

  const [globalExplainers, setGlobalExplainers] = useState([]);
  const [localExplainers, setLocalExplainers] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const { explainerToCreate, openExplainerCreator, closeExplainerCreator } =
    useModels();

  const taskName = session?.task_name;
  const modelName = run?.model_name;

  const fetchExplainers = useCallback(async () => {
    if (!taskName) return;
    try {
      setLoading(true);

      const fetchScope = async (explainerType) => {
        const [taskRelated, modelRelated] = await Promise.all([
          getComponents({
            selectTypes: [explainerType],
            relatedComponent: taskName,
          }),
          modelName
            ? getComponents({
                selectTypes: [explainerType],
                relatedComponent: modelName,
              })
            : Promise.resolve([]),
        ]);
        const seen = new Set();
        return [...taskRelated, ...modelRelated]
          .filter((obj) => {
            if (seen.has(obj.name)) return false;
            seen.add(obj.name);
            return true;
          })
          .filter((obj) => !obj.name.startsWith("Fit"));
      };

      const [globalResponse, localResponse] = await Promise.all([
        fetchScope("GlobalExplainer"),
        fetchScope("LocalExplainer"),
      ]);
      setGlobalExplainers(globalResponse);
      setLocalExplainers(localResponse);
    } catch (error) {
      console.error("Error fetching explainers:", error);
      enqueueSnackbar(t("explainers:error.fetchExplainers"), {
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  }, [taskName, modelName, enqueueSnackbar, t]);

  useEffect(() => {
    fetchExplainers();
  }, [fetchExplainers]);

  const query = searchQuery.trim().toLowerCase();
  const filteredGlobal = query
    ? globalExplainers.filter((expl) => matchesQuery(expl, query))
    : globalExplainers;
  const filteredLocal = query
    ? localExplainers.filter((expl) => matchesQuery(expl, query))
    : localExplainers;

  const renderSection = (title, explainers, scope) => (
    <Box sx={{ mb: 4 }}>
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{
          textTransform: "uppercase",
          letterSpacing: 0.5,
          fontWeight: 600,
          display: "block",
          mb: 2,
        }}
      >
        {title}
      </Typography>
      {explainers.length === 0 ? (
        <Typography
          variant="body2"
          sx={{ color: "text.secondary", textAlign: "center", py: 2 }}
        >
          {searchQuery
            ? t("models:label.noExplainersMatchSearch")
            : t("models:label.noCompatibleExplainersFound")}
        </Typography>
      ) : (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
          {explainers.map((explainer) => (
            <ModelListItem
              key={`${scope}-${explainer.name}`}
              model={explainer}
              draggable
              dragType="application/x-dashai-explainer"
              dragPayload={{ scope, name: explainer.name }}
              onClick={() =>
                openExplainerCreator({ scope, name: explainer.name })
              }
            />
          ))}
        </Box>
      )}
    </Box>
  );

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
          {t("models:label.availableExplainers")}
        </Typography>
      </Box>

      <Box sx={{ p: 4, flexShrink: 0 }}>
        <TextField
          fullWidth
          size="small"
          placeholder={t("explainers:label.searchExplainers")}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
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
        ) : (
          <>
            {renderSection(
              t("models:label.globalExplainers"),
              filteredGlobal,
              "global",
            )}
            {renderSection(
              t("models:label.localExplainers"),
              filteredLocal,
              "local",
            )}
          </>
        )}
      </Box>

      {explainerToCreate && (
        <InlineExplainerCreator
          open
          scope={explainerToCreate.scope}
          explainerConfig={{ runId: run.id, taskName, modelName }}
          preselectedExplainer={explainerToCreate.name}
          onCreated={onCreated}
          onCancel={closeExplainerCreator}
        />
      )}
    </SideBar>
  );
}

ExplainersSidebar.propTypes = {
  run: PropTypes.shape({
    id: PropTypes.number.isRequired,
  }).isRequired,
  session: PropTypes.shape({
    task_name: PropTypes.string,
  }),
  onCreated: PropTypes.func,
};
