import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import {
  FormControlLabel,
  Checkbox,
  Alert,
  Box,
  Link,
  Collapse,
  Typography,
  MenuItem,
  TextField,
  Divider,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { getComponentById, getComponents } from "../../../api/component";
import { useSnackbar } from "notistack";

/**
 * Component for selecting nested cross-validation option with informational messages.
 * When nested CV is enabled, allows configuring the inner loop splitter and folds.
 *
 * @param {boolean} useNestedCV - Whether nested cross-validation is enabled
 * @param {function} onChange - Callback when checkbox state changes
 * @param {object} innerConfig - Inner loop configuration { splitterType, nSplits }
 * @param {function} onInnerConfigChange - Callback when inner config changes
 * @param {object} outerSplit - session.splits object from the parent session
 * @param {number} maxInnerFolds - The maximum number of inner folds allowed
 */
function NestedCVSelector({
  useNestedCV,
  onChange,
  innerConfig,
  onInnerConfigChange,
  outerSplit,
  maxInnerFolds,
}) {
  const { t } = useTranslation(["models", "common"]);
  const { enqueueSnackbar } = useSnackbar();
  const [outerSplitterComponent, setOuterSplitterComponent] = useState(null);
  const [innerSplitterOptions, setInnerSplitterOptions] = useState([]);

  useEffect(() => {
    const getInnerSplitters = async () => {
      try {
        const outerSplitterComponent = await getComponentById(
          outerSplit.splitter_name,
        );
        setOuterSplitterComponent(outerSplitterComponent);

        const innerSplittersArray =
          outerSplitterComponent?.metadata?.compatibleInnerSplitters || [];

        const innerSplitterComponents = await Promise.all(
          innerSplittersArray.map((element) => getComponentById(element)),
        );

        setInnerSplitterOptions(innerSplitterComponents);
      } catch (error) {
        console.error("Error fetching splitters:", error);
        enqueueSnackbar(t("models:error.fetchingInnerSplitters"), {
          variant: "error",
        });
      }
    };

    getInnerSplitters();
  }, [outerSplit, enqueueSnackbar, t]);

  console.log("outerSplit:", outerSplit);
  console.log("innerConfig:", innerConfig);
  console.log("splitterType:", innerConfig?.splitterType);
  console.log("useNestedCV:", useNestedCV);

  const learnMoreLink = (
    <Link
      href="https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html"
      target="_blank"
      rel="noopener noreferrer"
      sx={{ color: "info.main", fontWeight: 600 }}
    >
      {t("common:learnMore")}
    </Link>
  );

  const handleInnerSplitterChange = (e) => {
    onInnerConfigChange({ ...innerConfig, splitterType: e.target.value });
  };

  const handleInnerFoldsChange = (e) => {
    const raw = e.target.value;
    onInnerConfigChange({
      ...innerConfig,
      nSplits: raw === "" ? "" : Number(raw),
    });
  };

  const foldsValue = innerConfig?.nSplits;
  const currentFolds = Number(foldsValue);
  const showFoldsWarning =
    foldsValue === "" ||
    !Number.isFinite(currentFolds) ||
    currentFolds < 2 ||
    currentFolds > maxInnerFolds;

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
      <FormControlLabel
        control={
          <Checkbox
            checked={useNestedCV}
            onChange={(e) => onChange(e.target.checked)}
          />
        }
        label={t("models:label.nestedCrossValidation")}
      />

      <Collapse in={!useNestedCV} unmountOnExit>
        <Alert severity="info" sx={{ py: 1.5 }}>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
            <div>{t("models:message.processChosenNormalHPO")}</div>
            <Typography variant="body2" color="text.secondary">
              {t("models:message.computationalCostNormalHPO")}
            </Typography>
          </Box>
        </Alert>
      </Collapse>

      <Collapse in={useNestedCV} unmountOnExit>
        <Alert severity="info" sx={{ py: 1.5 }}>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
            <div>
              {t("models:message.processChosenNestedCV") + " "}
              {learnMoreLink}
            </div>
            <Typography variant="body2" color="text.secondary">
              {t("models:message.computationalCostNestedCV")}
            </Typography>
          </Box>
        </Alert>
      </Collapse>

      <Collapse in={useNestedCV} unmountOnExit>
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 2,
            p: 2,
            border: "1px solid",
            borderColor: "divider",
            borderRadius: 1,
            bgcolor: "background.default",
          }}
        >
          <Typography variant="subtitle2">
            {t("models:label.innerLoopConfiguration")}
          </Typography>

          {/* Outer loop — read only for reference */}
          <Box sx={{ display: "flex", gap: 2 }}>
            <Box sx={{ flex: 1 }}>
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ mb: 0.5, display: "block" }}
              >
                {t("models:label.outerSplitter")}
              </Typography>
              <TextField
                value={outerSplitterComponent?.display_name || "-"}
                size="small"
                disabled
                fullWidth
                helperText={t("models:label.outerSplitterInherited")}
              />
            </Box>
            <Box sx={{ width: 120 }}>
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ mb: 0.5, display: "block" }}
              >
                {t("models:label.outerFolds")}
              </Typography>
              <TextField
                value={outerSplit?.n_splits ?? "-"}
                size="small"
                disabled
                fullWidth
              />
            </Box>
          </Box>

          <Divider />

          {/* Inner loop — configurable */}
          <Box sx={{ display: "flex", gap: 2 }}>
            <TextField
              select
              label={t("models:label.innerSplitter")}
              value={innerConfig?.splitterType}
              onChange={handleInnerSplitterChange}
              size="small"
              fullWidth
            >
              {innerSplitterOptions?.map((splitter) => (
                <MenuItem key={splitter.name} value={splitter.name}>
                  {splitter.display_name}
                </MenuItem>
              ))}
            </TextField>

            <TextField
              label={t("models:label.innerFolds")}
              type="number"
              value={foldsValue}
              onChange={handleInnerFoldsChange}
              size="small"
              sx={{ width: 120, flexShrink: 0 }}
              inputProps={{ min: 2, max: maxInnerFolds }}
            />
          </Box>
          {showFoldsWarning && (
            <Typography variant="body2" color="warning.main">
              {t("models:message.innerFoldsOutOfRange", {
                min: 2,
                max: maxInnerFolds,
              })}
            </Typography>
          )}
        </Box>
      </Collapse>
    </Box>
  );
}

NestedCVSelector.propTypes = {
  useNestedCV: PropTypes.bool.isRequired,
  onChange: PropTypes.func.isRequired,
  innerConfig: PropTypes.shape({
    splitterType: PropTypes.string,
    nSplits: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
  }).isRequired,
  onInnerConfigChange: PropTypes.func.isRequired,
  outerSplit: PropTypes.object,
  disabled: PropTypes.bool,
  maxInnerFolds: PropTypes.number,
};

export default NestedCVSelector;
