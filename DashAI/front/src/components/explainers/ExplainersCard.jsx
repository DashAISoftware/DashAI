import React, { useState } from "react";
import {
  Grid,
  Typography,
  IconButton,
  Paper,
  Box,
  CircularProgress,
} from "@mui/material";
import { useTheme, alpha } from "@mui/material/styles";
import DeleteConfirmationModal from "../threeSectionLayout/DeleteConfirmationModal";
import RunStatusDot from "../shared/RunStatusDot";
import DeleteIcon from "@mui/icons-material/Delete";
import ZoomInIcon from "@mui/icons-material/ZoomIn";
import PropTypes from "prop-types";
import ExplainersPlot from "./ExplainersPlot";
import { useNavigate } from "react-router-dom";
import {
  deleteExplainer,
  deleteExplainerPlotOverride,
  saveExplainerPlotOverride,
} from "../../api/explainer";
import { useTranslation } from "react-i18next";

const RUNNING_STATUSES = [1, 2]; // Delivered or Started

/**
 * GlobalExplainersCard
 * @param {*} explainer
 * @returns Component that render a card for the explainer
 */
export default function ExplainersCard({
  explainer,
  scope,
  onDelete,
  compact = false,
  displayName = null,
  cacheEntry = null,
  onCacheUpdate = null,
  isHighlighted = false,
}) {
  const theme = useTheme();
  const [open, setOpen] = useState(false);
  const { t } = useTranslation(["explainers"]);
  const isRunning = RUNNING_STATUSES.includes(explainer.status);

  function plotName(name) {
    return name.match(/[A-Z][a-z]+|[0-9]+/g).join(" ");
  }

  const navigate = useNavigate();

  const handleDeleteExplainer = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleConfirmDelete = async () => {
    await deleteExplainer(scope, explainer.id);
    handleClose();
    if (onDelete) {
      onDelete();
    } else {
      window.location.reload();
    }
  };

  const handleSaveOverride = async (index, figure) => {
    await saveExplainerPlotOverride(scope, explainer.id, index, figure);
  };

  const handleResetOverride = async (index) => {
    await deleteExplainerPlotOverride(scope, explainer.id, index);
  };

  if (compact) {
    return (
      <>
        <Paper
          variant="outlined"
          sx={{
            p: 4,
            bgcolor: "background.paper",
            borderColor: theme.palette.ui.border,
            borderRadius: 1,
            position: "relative",
            zIndex: isHighlighted ? 1 : 0,
            "@keyframes newItemHighlight": {
              "0%": { boxShadow: "none" },
              "20%": {
                boxShadow: `0 0 0 3px ${alpha(
                  theme.palette.primary.main,
                  0.65,
                )}, 0 0 24px 8px ${alpha(theme.palette.primary.main, 0.2)}`,
              },
              "100%": { boxShadow: "none" },
            },
            animation: isHighlighted
              ? "newItemHighlight 4s ease-in-out forwards"
              : "none",
          }}
        >
          <Grid container direction="column" gap={3}>
            <Grid
              item
              container
              direction="row"
              justifyContent="space-between"
              alignItems="center"
            >
              <Grid
                item
                sx={{ flex: 1, minWidth: 0, overflow: "hidden", mr: 2 }}
              >
                <Typography
                  variant="body1"
                  fontWeight="medium"
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 2,
                    flexWrap: "wrap",
                    wordBreak: "break-word",
                  }}
                >
                  {displayName || plotName(explainer.explainer_name)}
                  <RunStatusDot status={explainer.status} />
                </Typography>
              </Grid>
              <Grid sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <IconButton
                  size="small"
                  aria-label="delete"
                  color="error"
                  onClick={handleDeleteExplainer}
                  disabled={isRunning}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Grid>
            </Grid>

            {isRunning ? (
              <Box sx={{ py: 2, textAlign: "center" }}>
                <Typography variant="body2" color="text.secondary">
                  {t("explainers:label.explainerInProgress")}
                </Typography>
              </Box>
            ) : (
              <Grid sx={{ width: "100%" }}>
                <Box
                  sx={{ display: "flex", justifyContent: "flex-end", mb: 1 }}
                >
                  {/* Reserved slot for the future "generate story" action button.
                      Kept hidden until that feature lands. */}
                </Box>
                <ExplainersPlot
                  explainer={explainer}
                  scope={scope}
                  onSaveOverride={handleSaveOverride}
                  onResetOverride={handleResetOverride}
                  cacheEntry={cacheEntry}
                  onCacheUpdate={onCacheUpdate}
                />
              </Grid>
            )}
          </Grid>
        </Paper>

        <DeleteConfirmationModal
          open={open}
          onClose={handleClose}
          onConfirm={handleConfirmDelete}
          content={t("explainers:label.deleteExplainerConfirmation")}
        />
      </>
    );
  }

  // Full mode for standalone page
  return (
    <Paper elevation={3} sx={{ width: "100%" }}>
      <Grid container item p={8} gap={4}>
        <Grid
          item
          container
          direction={"row"}
          justifyContent={"space-between"}
          alignItems={"center"}
        >
          <Grid>
            <Typography variant="h6">
              {plotName(explainer.explainer_name)}
            </Typography>
          </Grid>
          <Grid sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            {isRunning && <CircularProgress size={22} />}
            <IconButton
              aria-label="zoomin"
              disabled={isRunning}
              onClick={() => {
                navigate(
                  `/app/explainers/explainer/${scope}/${explainer.run_id}/${explainer.id}`,
                );
              }}
            >
              <ZoomInIcon />
            </IconButton>
            <IconButton
              aria-label="delete"
              color="error"
              onClick={handleDeleteExplainer}
              disabled={isRunning}
            >
              <DeleteIcon />
            </IconButton>
            <DeleteConfirmationModal
              open={open}
              onClose={handleClose}
              onConfirm={handleConfirmDelete}
              content={t("explainers:label.deleteExplainerConfirmation")}
            />
          </Grid>
        </Grid>
        <ExplainersPlot explainer={explainer} scope={scope} />
      </Grid>
    </Paper>
  );
}

ExplainersCard.propTypes = {
  explainer: PropTypes.shape({
    id: PropTypes.number,
    name: PropTypes.string,
    run_id: PropTypes.number,
    explainer_name: PropTypes.string,
    explanation_path: PropTypes.string,
    plot_path: PropTypes.string,
    parameters: PropTypes.objectOf(
      PropTypes.oneOfType([
        PropTypes.number,
        PropTypes.string,
        PropTypes.arrayOf(PropTypes.string),
      ]),
    ),
    created: PropTypes.string,
    status: PropTypes.number,
  }).isRequired,
  scope: PropTypes.string.isRequired,
  onDelete: PropTypes.func,
  compact: PropTypes.bool,
  displayName: PropTypes.string,
  cacheEntry: PropTypes.shape({
    items: PropTypes.array,
    selectedGroups: PropTypes.object,
  }),
  onCacheUpdate: PropTypes.func,
  isHighlighted: PropTypes.bool,
};
