import { useState, useEffect, useMemo, useRef } from "react";
import PropTypes from "prop-types";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Button,
  Checkbox,
  FormControlLabel,
  Stack,
  CircularProgress,
  Alert,
  Divider,
  Chip,
  IconButton,
  TextField,
} from "@mui/material";
import { Close as CloseIcon, Check as CheckIcon } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import {
  getFoldMetrics,
  runStatisticalTest,
  saveStatisticalTestResults,
} from "../../api/statisticalTests";
import SingleTestResult from "./SingleTestResult";
import PerRunResults from "./PerRunResults";

export default function StatisticalTestsModal({
  test,
  runs = [],
  session,
  open = false,
  onClose,
}) {
  const { t } = useTranslation(["models", "common"]);

  const [selectedMetric, setSelectedMetric] = useState("");
  const [selectedSplit, setSelectedSplit] = useState("validation");
  const [selectedRuns, setSelectedRuns] = useState([]);
  const [alpha, setAlpha] = useState(0.05);
  const [alternative, setAlternative] = useState("two-sided");
  const [correctionMethod, setCorrectionMethod] = useState("");
  const [availableMetrics, setAvailableMetrics] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);
  const [perRunResults, setPerRunResults] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [customName, setCustomName] = useState("");
  const [customDescription, setCustomDescription] = useState("");
  const resultsRef = useRef(null);

  // backend metadata
  const minRuns = test?.metadata?.min_runs ?? 2;
  const maxRuns = test?.metadata?.max_runs ?? Infinity;
  const supportsAlternative = test?.metadata?.supports_alternative === true;
  const supportsCorrection = test?.metadata?.supports_correction === true;
  // Per-run tests (e.g. Shapiro-Wilk normality) run independently on each
  // selected run instead of producing a single omnibus result.
  const isPerRun = test?.metadata?.per_run === true;
  const testIdentifier = test?.name; // registry name expected by the API
  const testTitle = test?.metadata?.name || test?.display_name || test?.name;

  const finishedRuns = useMemo(
    () => runs.filter((run) => run.status === 3),
    [runs],
  );

  const runIds = useMemo(
    () => selectedRuns.map((run) => run.id),
    [selectedRuns],
  );

  const runNames = useMemo(() => {
    const names = {};
    selectedRuns.forEach((run) => {
      names[run.id.toString()] = run.name;
    });
    return names;
  }, [selectedRuns]);

  const countValid =
    selectedRuns.length >= minRuns && selectedRuns.length <= maxRuns;
  const atMax = selectedRuns.length >= maxRuns;

  const runsRequirementText = useMemo(() => {
    if (maxRuns === Infinity) {
      return t("models:label.selectAtLeastRuns", { min: minRuns });
    }
    if (minRuns === maxRuns) {
      return t("models:label.selectExactlyRuns", { count: minRuns });
    }
    return t("models:label.selectBetweenRuns", { min: minRuns, max: maxRuns });
  }, [minRuns, maxRuns, t]);

  // Reset state each time the modal opens
  useEffect(() => {
    if (open) {
      setSelectedRuns([]);
      setResults(null);
      setPerRunResults(null);
      setSaved(false);
      setError(null);
      setCustomName("");
      setCustomDescription("");
      setAlternative("two-sided");
      setCorrectionMethod("");
      setSelectedMetric("");
      setSelectedSplit("validation");
    }
  }, [open, testIdentifier]);

  // Derive available metrics from finished runs + chosen split
  useEffect(() => {
    if (finishedRuns.length > 0) {
      const metricsSet = new Set();
      finishedRuns.forEach((run) => {
        const metricsObj =
          selectedSplit === "train"
            ? run.train_metrics
            : run.validation_metrics;
        if (metricsObj && typeof metricsObj === "object") {
          Object.keys(metricsObj).forEach((metric) => metricsSet.add(metric));
        }
      });
      const metricsList = Array.from(metricsSet).sort();
      setAvailableMetrics(metricsList);
      if (metricsList.length > 0 && !selectedMetric) {
        setSelectedMetric(metricsList[0]);
      }
    }
  }, [selectedSplit, finishedRuns, selectedMetric]);

  // Smoothly scroll to the results as soon as they appear
  useEffect(() => {
    if ((results || perRunResults) && resultsRef.current) {
      requestAnimationFrame(() => {
        resultsRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      });
    }
  }, [results, perRunResults]);

  const handleRunToggle = (run) => {
    setSelectedRuns((prev) => {
      const isSelected = prev.some((r) => r.id === run.id);
      if (isSelected) return prev.filter((r) => r.id !== run.id);
      if (prev.length >= maxRuns) return prev; // enforce max
      return [...prev, run];
    });
  };

  useEffect(() => {
    if (supportsAlternative) {
      if (selectedRuns.length >= 3) {
        setAlternative("two-sided");
      }
    }
  }, [selectedRuns.length, supportsAlternative]);

  useEffect(() => {
    if (supportsCorrection) {
      if (selectedRuns.length >= 3) {
        setCorrectionMethod((prev) => (prev ? prev : "holm"));
      } else {
        setCorrectionMethod("");
      }
    }
  }, [selectedRuns.length, supportsCorrection]);

  const buildTestParams = () => {
    const params = {};

    if (supportsAlternative) {
      params.alternative = selectedRuns.length >= 3 ? "two-sided" : alternative;
    }

    if (supportsCorrection && selectedRuns.length >= 3 && correctionMethod) {
      params.correction_method = correctionMethod;
    }

    return params;
  };

  const handleExecuteTest = async () => {
    if (!countValid) {
      setError(runsRequirementText);
      return;
    }
    if (!selectedMetric) {
      setError(t("models:error.selectMetric"));
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);
    setPerRunResults(null);
    setSaved(false);
    setCustomName("");
    setCustomDescription("");

    try {
      const params = buildTestParams();

      if (isPerRun) {
        // Fan-out: one independent request per selected run, in parallel.
        // Each request sends a single run, so len(scores) == 1 on the backend
        // and the per-test contract stays unchanged.
        const perRun = await Promise.all(
          selectedRuns.map(async (run) => {
            const metrics = await getFoldMetrics(run.id, selectedSplit);
            const data = metrics[selectedMetric] || [];
            const resp = await runStatisticalTest({
              test_name: testIdentifier,
              metric_name: selectedMetric,
              metric_split: selectedSplit,
              run_ids: [run.id],
              run_names: { [run.id.toString()]: run.name },
              fold_metrics: { [run.id]: data },
              alpha,
              params,
            });
            return { id: run.id, name: run.name, resp };
          }),
        );
        setPerRunResults(perRun);
        setError(null);
        return;
      }

      const foldMetricsData = {};
      for (const run of selectedRuns) {
        const metrics = await getFoldMetrics(run.id, selectedSplit);
        foldMetricsData[run.id] = metrics[selectedMetric] || [];
      }

      const testResponse = await runStatisticalTest({
        test_name: testIdentifier,
        metric_name: selectedMetric,
        metric_split: selectedSplit,
        run_ids: runIds,
        run_names: runNames,
        fold_metrics: foldMetricsData,
        alpha,
        params,
      });

      setResults(testResponse);
      setError(null);
    } catch (err) {
      console.error("Error executing statistical test:", err);
      setError(
        err.response?.data?.detail || t("models:error.failedToExecuteTest"),
      );
      setResults(null);
      setPerRunResults(null);
    } finally {
      setLoading(false);
    }
  };

  // Assemble the payload(s) to persist from the currently displayed result(s).
  // Single omnibus result is one item, per-run batch (Shapiro) is one per run.
  const buildSavePayload = () => {
    const modelSessionId = session?.id ?? null;
    const name = customName.trim() || null;
    const description = customDescription.trim() || null;

    if (isPerRun && perRunResults) {
      return perRunResults.map(({ id, name: runName, resp }) => ({
        test_name: test.display_name,
        metric_name: selectedMetric,
        metric_split: selectedSplit,
        alpha: resp.alpha,
        significant: resp.significant,
        run_ids: [id],
        run_names: { [id.toString()]: runName },
        statistic: resp.statistic ?? null,
        p_value: resp.p_value ?? null,
        interpretation: resp.interpretation ?? null,
        params: {},
        details: resp.details ?? null,
        posthoc: resp.posthoc ?? null,
        model_session_id: modelSessionId,
        name,
        description,
      }));
    }

    if (results) {
      return [
        {
          test_name: test.display_name,
          metric_name: selectedMetric,
          metric_split: selectedSplit,
          alpha: results.alpha,
          significant: results.significant,
          run_ids: selectedRuns.map((run) => run.id),
          run_names: runNames,
          statistic: results.statistic ?? null,
          p_value: results.p_value ?? null,
          interpretation: results.interpretation ?? null,
          params: buildTestParams(),
          details: results.details ?? null,
          posthoc: results.posthoc ?? null,
          model_session_id: modelSessionId,
          name,
          description,
        },
      ];
    }

    return [];
  };

  const handleSave = async () => {
    const payload = buildSavePayload();
    if (payload.length === 0) return;

    setSaving(true);
    setError(null);
    try {
      await saveStatisticalTestResults(payload);
      setSaved(true);
    } catch (err) {
      console.error("Error saving statistical test:", err);
      setError(
        err.response?.data?.detail || t("models:error.failedToSaveTest"),
      );
    } finally {
      setSaving(false);
    }
  };

  if (!test) return null;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{ sx: { minHeight: "500px" } }}
    >
      <DialogTitle sx={{ bgcolor: "background.paper" }}>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          {testTitle}
          <IconButton
            onClick={onClose}
            size="small"
            sx={{ color: "text.secondary" }}
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers sx={{ bgcolor: "background.paper" }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {typeof error === "string"
              ? error
              : error?.msg || JSON.stringify(error)}
          </Alert>
        )}

        {/* Metric and Split selectors */}
        <Box sx={{ display: "flex", gap: 2, mb: 3 }}>
          <FormControl sx={{ flex: 1, minWidth: 200 }}>
            <InputLabel>{t("common:metric")}</InputLabel>
            <Select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              label={t("common:metric")}
              disabled={availableMetrics.length === 0}
            >
              {availableMetrics.map((metric) => (
                <MenuItem key={metric} value={metric}>
                  {metric}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl sx={{ flex: 1, minWidth: 200 }}>
            <InputLabel>{t("common:split")}</InputLabel>
            <Select
              value={selectedSplit}
              onChange={(e) => setSelectedSplit(e.target.value)}
              label={t("common:split")}
            >
              {/* A paired test needs one sample per fold, and folds only
                  exist for train and validation: the reserved rows yield a
                  single score. */}
              <MenuItem value="train">{t("common:train")}</MenuItem>
              <MenuItem value="validation">{t("common:validation")}</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Runs to compare */}
        <Box sx={{ mb: 3 }}>
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              mb: 1.5,
            }}
          >
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              {t("models:label.modelsToCompare")}
            </Typography>
            <Typography
              variant="caption"
              sx={{ color: countValid ? "success.main" : "text.secondary" }}
            >
              {selectedRuns.length} / {runsRequirementText}
            </Typography>
          </Box>

          {finishedRuns.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              {t("models:label.noFinishedRuns")}
            </Typography>
          ) : (
            <Stack spacing={1} sx={{ pl: 1 }}>
              {finishedRuns.map((run) => {
                const isSelected = selectedRuns.some((r) => r.id === run.id);
                const selIdx = selectedRuns.findIndex((r) => r.id === run.id);
                return (
                  <FormControlLabel
                    key={run.id}
                    control={
                      <Checkbox
                        checked={isSelected}
                        disabled={!isSelected && atMax}
                        onChange={() => handleRunToggle(run)}
                      />
                    }
                    label={
                      <Box
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          gap: 0.75,
                        }}
                      >
                        <Box>
                          <Typography variant="body2">{run.name}</Typography>
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{ display: "block", mt: 0.25 }}
                          >
                            {new Date(run.created).toLocaleDateString()}
                          </Typography>
                        </Box>
                        {supportsAlternative && selIdx === 0 && (
                          <Chip
                            label={t("models:label.model1")}
                            size="small"
                            color="primary"
                            variant="outlined"
                            sx={{ fontSize: "0.65rem", height: 18 }}
                          />
                        )}
                        {supportsAlternative && selIdx === 1 && (
                          <Chip
                            label={t("models:label.model2")}
                            size="small"
                            color="secondary"
                            variant="outlined"
                            sx={{ fontSize: "0.65rem", height: 18 }}
                          />
                        )}
                      </Box>
                    }
                  />
                );
              })}
            </Stack>
          )}
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Alpha + hypothesis/correction options */}
        <Box
          sx={{
            display: "flex",
            gap: 3,
            alignItems: "flex-start",
            flexWrap: "wrap",
          }}
        >
          <Box sx={{ flex: 1, minWidth: 220 }}>
            <Box
              sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}
            >
              <Typography variant="body2">
                {t("models:label.significanceLevel")} (α)
              </Typography>
              <Typography
                variant="body2"
                sx={{ fontWeight: 600, color: "primary.main" }}
              >
                {alpha.toFixed(2)}
              </Typography>
            </Box>
            <Slider
              value={alpha}
              onChange={(e, newValue) => setAlpha(newValue)}
              min={0.01}
              max={0.2}
              step={0.01}
              marks={[
                { value: 0.01, label: "0.01" },
                { value: 0.1, label: "0.1" },
                { value: 0.2, label: "0.2" },
              ]}
              valueLabelDisplay="off"
              disabled={loading}
            />
          </Box>

          {supportsAlternative ? (
            <Box sx={{ flex: 1, minWidth: 220 }}>
              <FormControl fullWidth size="small">
                <InputLabel>
                  {t("models:label.alternativeHypothesis")}
                </InputLabel>
                <Select
                  value={alternative}
                  onChange={(e) => setAlternative(e.target.value)}
                  label={t("models:label.alternativeHypothesis")}
                  disabled={selectedRuns.length >= 3}
                >
                  <MenuItem value="two-sided">
                    {t("models:label.twoSided")}
                  </MenuItem>
                  <MenuItem value="greater">
                    {t("models:label.greater")}
                  </MenuItem>
                  <MenuItem value="less">{t("models:label.less")}</MenuItem>
                </Select>
              </FormControl>
              {selectedRuns.length === 2 && (
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ mt: 0.5, display: "block" }}
                >
                  {t("models:label.model1")}:{" "}
                  <strong>{selectedRuns[0].name}</strong>
                  <br />
                  {t("models:label.model2")}:{" "}
                  <strong>{selectedRuns[1].name}</strong>
                </Typography>
              )}
            </Box>
          ) : null}

          {supportsCorrection ? (
            <Box sx={{ flex: 1, minWidth: 220 }}>
              <FormControl fullWidth size="small">
                <InputLabel>{t("models:label.correctionMethod")}</InputLabel>
                <Select
                  value={correctionMethod}
                  onChange={(e) => setCorrectionMethod(e.target.value)}
                  label={t("models:label.correctionMethod")}
                  disabled={selectedRuns.length < 3}
                >
                  <MenuItem value="holm">Holm</MenuItem>
                  <MenuItem value="bonferroni">Bonferroni</MenuItem>
                  <MenuItem value="benjamini_hochberg">
                    Benjamini-Hochberg
                  </MenuItem>
                </Select>
              </FormControl>
            </Box>
          ) : null}
        </Box>

        {/* Results */}
        {!isPerRun && results && (
          <SingleTestResult ref={resultsRef} result={results} />
        )}

        {isPerRun && perRunResults && (
          <PerRunResults
            ref={resultsRef}
            results={perRunResults}
            title={testTitle}
            alpha={alpha}
          />
        )}

        {/* Optional custom name + description for the saved result */}
        {(results || perRunResults) && (
          <Box
            sx={{
              mt: 3,
              pt: 2,
              borderTop: "1px solid",
              borderColor: "divider",
            }}
          >
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1.5 }}>
              {t("models:label.saveDetails")}
            </Typography>
            <Stack spacing={2}>
              <TextField
                label={t("models:label.testName")}
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
                placeholder={testTitle}
                size="small"
                fullWidth
                disabled={saved}
                inputProps={{ maxLength: 100 }}
                helperText={
                  <Box
                    component="span"
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      gap: 1,
                    }}
                  >
                    <span>{t("models:label.testNameHelp")}</span>
                    <span>{customName.length}/100</span>
                  </Box>
                }
              />
              <TextField
                label={t("models:label.testDescription")}
                value={customDescription}
                onChange={(e) => setCustomDescription(e.target.value)}
                size="small"
                fullWidth
                multiline
                minRows={2}
                disabled={saved}
                inputProps={{ maxLength: 500 }}
                helperText={`${customDescription.length}/500`}
                FormHelperTextProps={{ sx: { textAlign: "right", mx: 0 } }}
              />
            </Stack>
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ p: 2, bgcolor: "background.paper" }}>
        <Button variant="outlined" onClick={onClose} disabled={loading}>
          {t("common:cancel")}
        </Button>

        {(results || perRunResults) && (
          <Button
            variant="outlined"
            color="success"
            onClick={handleSave}
            disabled={saving || saved}
            startIcon={
              saving ? (
                <CircularProgress size={18} />
              ) : saved ? (
                <CheckIcon />
              ) : null
            }
            sx={{ minWidth: 160 }}
          >
            {saved
              ? t("models:label.resultSaved")
              : t("models:label.saveResult")}
          </Button>
        )}

        <Button
          variant="contained"
          onClick={handleExecuteTest}
          disabled={loading || !countValid || !selectedMetric}
          sx={{ minWidth: 140 }}
        >
          {loading ? (
            <>
              <CircularProgress size={20} sx={{ mr: 1 }} />
              {t("common:executing")}
            </>
          ) : (
            t("common:execute")
          )}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

StatisticalTestsModal.propTypes = {
  test: PropTypes.shape({
    name: PropTypes.string,
    display_name: PropTypes.string,
    metadata: PropTypes.object,
  }),
  runs: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      name: PropTypes.string.isRequired,
      status: PropTypes.number.isRequired,
    }),
  ),
  session: PropTypes.object,
  open: PropTypes.bool,
  onClose: PropTypes.func.isRequired,
};
