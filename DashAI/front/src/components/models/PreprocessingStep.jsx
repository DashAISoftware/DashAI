import { useCallback, useEffect, useState } from "react";
import PropTypes from "prop-types";
import { Box, CircularProgress, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import {
  getModelSessionById,
  updateSessionConverters,
} from "../../api/modelSession";
import { getDatasetTypes } from "../../api/datasets";
import { useModels } from "./ModelsContext";
import { useExplorersAndConverters } from "../notebooks/context/ExplorersAndConvertersContext";
import AppliedConvertersView from "./modelSession/AppliedConvertersView";
import SessionConvertersRightBar from "./modelSession/SessionConvertersRightBar";
import StepperNavigationFooter from "../shared/StepperNavigationFooter";

/**
 * Second wizard step (of three): configure session converters. The session
 * record already exists by the time this step is reachable (created at the
 * end of step 0, in CreateSessionSteps.jsx) — this step's job is only to
 * let the user add/remove converters against it, via the real
 * `/model-session/{id}/converters` endpoint. Converters are configured from
 * the sidebar pushed into `sessionRightContent` (SessionConvertersRightBar);
 * the center panel renders a card per already-configured converter
 * (AppliedConvertersView). Adding a converter here only stores its
 * configuration (scope/params) — nothing is actually executed until the
 * wizard finalizes, so there is no apply-and-poll cycle to track. The
 * session itself, not `newExp`, is the source of truth here —
 * `newExp.converters` was only ever meaningful back when converters were
 * client-side-only, before step 1 existed.
 */
function PreprocessingStep({
  newExp,
  dataset,
  modelSessionId,
  refreshTrigger,
  isActive = true,
  onBack,
  onCreateSession,
}) {
  const { setSessionRightContent } = useModels();
  const { t } = useTranslation(["models", "datasets", "common"]);
  const theme = useTheme();
  const { setPendingDropTool } = useExplorersAndConverters();
  const [rawColumnTypes, setRawColumnTypes] = useState({});
  const [isDragOver, setIsDragOver] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const [session, setSession] = useState(null);

  // Mirrors the notebook's NotebookView.jsx drop target: same window-level
  // dragstart/dragend listeners driving the same "is a converter card being
  // dragged right now" overlay, so dropping one here behaves exactly like
  // dropping it onto the sidebar's own cards.
  useEffect(() => {
    const onStart = (e) => {
      if (e.dataTransfer.types.includes("application/x-dashai-tool")) {
        setIsDragging(true);
      }
    };
    const onEnd = () => {
      setIsDragging(false);
      setIsDragOver(false);
    };
    window.addEventListener("dragstart", onStart);
    window.addEventListener("dragend", onEnd);
    return () => {
      window.removeEventListener("dragstart", onStart);
      window.removeEventListener("dragend", onEnd);
    };
  }, []);

  const handleDragOver = (e) => {
    if (!e.dataTransfer.types.includes("application/x-dashai-tool")) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = "copy";
  };

  const handleDragEnter = (e) => {
    if (!e.dataTransfer.types.includes("application/x-dashai-tool")) return;
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    const related = e.relatedTarget;
    if (!related || !e.currentTarget.contains(related)) {
      setIsDragOver(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    try {
      const tool = JSON.parse(
        e.dataTransfer.getData("application/x-dashai-tool"),
      );
      if (tool?.name) setPendingDropTool(tool);
    } catch {
      // ignore invalid drops
    }
  };

  // The raw dataset's column types never change while this step is mounted
  // (converters are no longer applied for real, so there's no
  // "current"/preprocessed column set to keep re-reading — see Task 10) —
  // fetched once here rather than alongside every session refresh.
  useEffect(() => {
    let cancelled = false;
    getDatasetTypes(dataset.id)
      .then((types) => {
        if (!cancelled) setRawColumnTypes(types || {});
      })
      .catch((error) => {
        console.error("Error fetching dataset column types:", error);
      });
    return () => {
      cancelled = true;
    };
  }, [dataset.id]);

  // Stable across renders (deps only on modelSessionId) — this is passed to
  // SessionConvertersRightBar as `onConvertersChanged`, which in turn feeds
  // its own `SessionFormSection` useMemo alongside `session` itself. That
  // memo's whole purpose is keeping the ConfigureToolModal form mounted
  // while the user is mid-configuration, so `session` must only change at
  // well-defined boundaries (mount, an explicit remove, or a converter
  // save finishing) — or an open modal would remount and silently lose the
  // user's in-progress scope/parameter selection.
  // GET /model-session/{id} never returns a nested `dataset` object (only
  // `dataset_id`), so every `session` this component hands downstream is
  // patched with the `dataset` prop it already has from step 0 —
  // ScopeStepSessionConverter still needs `session.dataset.file_path` to
  // preview the raw dataset while picking a converter's scope columns.
  const setSessionWithDataset = useCallback(
    (nextSession) =>
      setSession(
        nextSession
          ? { ...nextSession, dataset: nextSession.dataset || dataset }
          : nextSession,
      ),
    [dataset],
  );

  const refreshSession = useCallback(async () => {
    try {
      const fresh = await getModelSessionById(modelSessionId);
      setSessionWithDataset(fresh);
      return fresh;
    } catch (error) {
      console.error("Error fetching model session:", error);
      return null;
    }
  }, [modelSessionId, setSessionWithDataset]);

  useEffect(() => {
    refreshSession();
    // refreshTrigger isn't read inside refreshSession — it's a pure
    // re-run signal, bumped by CreateSessionSteps every time step 0
    // advances back into this step, so a split change that invalidated
    // converters (see that component's `converters_invalidated` handling)
    // is picked up even though this component never unmounts.
  }, [refreshSession, refreshTrigger]);

  // Removal is initiated here (unlike adding, which lives entirely inside
  // FormSessionConverterSection via the sidebar).
  const handleRemoveConverter = async (index) => {
    if (!session) return;
    const nextConverters = (session.converters || []).slice(0, index);
    try {
      const updated = await updateSessionConverters(
        modelSessionId,
        nextConverters,
      );
      setSessionWithDataset(updated);
    } catch (error) {
      console.error("Error removing converter:", error);
    }
  };

  // Push the converters sidebar into the shared right-bar slot. Gated on
  // `isActive`, exactly like DatasetSplitStep's own push: this component
  // stays mounted (hidden via CSS, not unmounted) once reached, and its state
  // keeps changing in the background — removing a converter calls
  // refreshSession, which updates `session` and re-runs this effect. Without
  // the gate, that would silently replace step 0's SplitDatasetRows if the
  // user had already clicked "Atrás". The slot is yielded by the previous
  // run's cleanup below, and `isActive` is in the deps so it's reclaimed on
  // the way back in.
  useEffect(() => {
    if (!isActive) return;
    setSessionRightContent(
      session ? (
        <SessionConvertersRightBar
          session={session}
          inputColumnNames={newExp.input_columns}
          rawColumnTypes={rawColumnTypes}
          onConvertersChanged={refreshSession}
        />
      ) : (
        <Box
          sx={{
            display: "flex",
            height: "100%",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <CircularProgress size={24} />
        </Box>
      ),
    );
    return () => setSessionRightContent(null);
  }, [
    session,
    newExp.input_columns,
    rawColumnTypes,
    refreshSession,
    setSessionRightContent,
    isActive,
  ]);

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        minHeight: 0,
      }}
    >
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5" component="h1">
          {t("models:label.sessionConverters")}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {t("models:label.sessionConvertersDescription")}
        </Typography>
      </Box>
      <Box
        onDragOver={handleDragOver}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        sx={{
          flex: 1,
          minHeight: 0,
          overflowY: "auto",
          pt: 2,
          position: "relative",
          outline: isDragOver
            ? `2px dashed ${theme.palette.primary.main}`
            : isDragging
              ? `2px dashed ${theme.palette.divider}`
              : "none",
          transition: "outline 0.15s",
        }}
      >
        {isDragging && (
          <Box
            sx={{
              position: "absolute",
              inset: 0,
              zIndex: 10,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              bgcolor: isDragOver
                ? `${theme.palette.primary.main}14`
                : theme.palette.action.hover,
              pointerEvents: "none",
              transition: "background-color 0.15s",
            }}
          >
            <Typography
              variant="h6"
              sx={{
                color: isDragOver
                  ? theme.palette.primary.main
                  : theme.palette.text.secondary,
                fontWeight: 600,
                pointerEvents: "none",
                transition: "color 0.15s",
              }}
            >
              {t("datasets:label.dropToolHere")}
            </Typography>
          </Box>
        )}
        {session ? (
          <AppliedConvertersView
            session={session}
            onRemoveConverter={handleRemoveConverter}
          />
        ) : (
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              py: 8,
            }}
          >
            <CircularProgress />
          </Box>
        )}
      </Box>
      <StepperNavigationFooter onBack={onBack} onNext={onCreateSession} />
    </Box>
  );
}

PreprocessingStep.propTypes = {
  newExp: PropTypes.shape({
    input_columns: PropTypes.arrayOf(PropTypes.string),
  }).isRequired,
  dataset: PropTypes.object.isRequired,
  modelSessionId: PropTypes.oneOfType([PropTypes.string, PropTypes.number])
    .isRequired,
  refreshTrigger: PropTypes.number.isRequired,
  isActive: PropTypes.bool,
  onBack: PropTypes.func.isRequired,
  onCreateSession: PropTypes.func.isRequired,
};

export default PreprocessingStep;
