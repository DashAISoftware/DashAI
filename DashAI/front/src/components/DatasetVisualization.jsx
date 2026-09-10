import { useCallback, useState, useEffect } from "react";
import {
  Button,
  Grid,
  Typography,
  CircularProgress,
  Box,
  Alert,
  Divider,
  Tab,
  Tooltip,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { AddCircleOutline as AddIcon } from "@mui/icons-material";
import PillTabs from "./shared/PillTabs";
import {
  getDatasetInfo,
  getDatasetFile,
  getDatasetFileFiltered,
  getDatasetTypes,
} from "../api/datasets";
import { useTourContext } from "./tour/TourProvider";
import { formatDate } from "../pages/results/constants/formatDate";
import Header from "./notebooks/dataset/header/Header";
import OverviewTab from "./notebooks/dataset/tabs/OverviewTab";
import { NumericTab } from "./notebooks/dataset/tabs/NumericTab";
import { CategoricalTab } from "./notebooks/dataset/tabs/CategoricalTab";
import QualityTab from "./notebooks/dataset/tabs/QualityTab";
import CorrelationsTab from "./notebooks/dataset/tabs/CorrelationsTab";
import { QualityAlerts } from "./notebooks/dataset/QualityAlerts";
import { TextTab } from "./notebooks/dataset/tabs/TextTab";
import { useTranslation } from "react-i18next";
import { useDatasetsAndNotebooks } from "./custom/contexts/DatasetsAndNotebooksContext";
import { useModels } from "./models/ModelsContext";
/**
 * Component to visualize dataset information including quality metrics, statistics, and data preview.
 * Can be used across different modules (Notebooks, Models) with customizable action buttons.
 * @param {Object} props
 * @param {Object} props.dataset - Dataset object containing id, name, file_path, status, and created date
 * @param {Function} props.onNewItem - Callback function when "New Item" button is clicked
 * @param {string} [props.newItemButtonText="New Item"] - Custom text for the action button (e.g., "New Notebook", "New Session")
 * @param {Array} [props.existingItems=[]] - Array of existing items (notebooks/sessions) for validation
 */
export default function DatasetVisualization({
  dataset,
  onNewItem,
  newItemButtonText = "New Item",
  tourContextType = null,
}) {
  const { t } = useTranslation(["datasets", "common"]);
  const theme = useTheme();
  const datasetsContext = useDatasetsAndNotebooks();
  const modelsContext = useModels();
  const setSharedDatasetInfo =
    datasetsContext?.setDatasetInfo ??
    modelsContext?.setDatasetInfo ??
    (() => {});
  const tab = datasetsContext?.datasetTab ?? modelsContext?.datasetTab ?? 0;
  const setTab =
    datasetsContext?.setDatasetTab ??
    modelsContext?.setDatasetTab ??
    (() => {});
  const scrollToColumn =
    datasetsContext?.scrollToColumn ?? modelsContext?.scrollToColumn ?? null;
  const setScrollToColumn =
    datasetsContext?.setScrollToColumn ??
    modelsContext?.setScrollToColumn ??
    (() => {});

  const [datasetInfo, setDatasetInfo] = useState(null);
  const [columnTypes, setColumnTypes] = useState({});
  const tourContext = useTourContext();

  useEffect(() => {
    if (sessionStorage.getItem("startDatasetViewTour") === "true") {
      sessionStorage.removeItem("startDatasetViewTour");
      // Esperar más tiempo para que termine todo el ajuste de scroll
      setTimeout(() => {
        if (tourContext && typeof tourContext.startTour === "function") {
          tourContext.startTour();
        }
      }, 1500);
    }
  }, [tourContext]);

  const fetchDatasetInfo = async () => {
    const isProcessing = !(dataset.status === 3 || dataset.status === 4);
    if (isProcessing && fetchDatasets) {
      setTimeout(() => {
        fetchDatasets();
      }, 1000);
      return;
    }
    try {
      const info = await getDatasetInfo(Number(dataset.id));
      setDatasetInfo(info);
    } catch (error) {
      setDatasetInfo(null);
    }
  };

  useEffect(() => {
    setTab(0);

    if (!dataset || dataset.status !== 3) {
      setDatasetInfo(null);
      setSharedDatasetInfo(null);
      setColumnTypes({});
      return;
    }

    const fetchDatasetInfo = async () => {
      try {
        const info = await getDatasetInfo(Number(dataset.id));
        setDatasetInfo(info);
        setSharedDatasetInfo(info);
      } catch (error) {
        setDatasetInfo(null);
        setSharedDatasetInfo(null);
      }
    };

    const fetchColumnTypes = async () => {
      try {
        const types = await getDatasetTypes(Number(dataset.id));
        setColumnTypes(types);
      } catch (error) {
        setColumnTypes({});
      }
    };

    fetchDatasetInfo();
    fetchColumnTypes();

    return () => setSharedDatasetInfo(null);
  }, [dataset?.id, dataset?.status]);

  const fetchDatasetPage = useCallback(
    async (page, pageSize, filterModel, sortModel) => {
      const isProcessing =
        dataset && !(dataset.status === 3 || dataset.status === 4);
      if (!dataset || isProcessing) return { rows: [], total: 0 };
      try {
        const hasFilters =
          filterModel?.items?.length > 0 || (sortModel && sortModel.length > 0);

        const data = hasFilters
          ? await getDatasetFileFiltered(
              dataset.file_path,
              page,
              pageSize,
              filterModel,
              sortModel,
            )
          : await getDatasetFile(dataset.file_path, page, pageSize);

        return { rows: data.rows ?? [], total: data.total ?? 0 };
      } catch (error) {
        return { rows: [], total: 0 };
      }
    },
    [
      dataset && dataset.file_path,
      dataset && dataset.status,
      dataset && dataset.id,
    ],
  );

  const updateDatasetInfo = async () => {
    fetchDatasetInfo();
    try {
      const types = await getDatasetTypes(Number(dataset.id));
      setColumnTypes(types);
    } catch (error) {
      // keep existing types on failure
    }
  };

  if (!dataset) {
    return (
      <Box
        sx={{ display: "flex", justifyContent: "center", alignItems: "center" }}
      >
        <CircularProgress sx={{ color: theme.palette.primary.main }} />
        <Typography>{t("common:loading")}</Typography>
      </Box>
    );
  }

  const status = dataset.status;
  const isProcessing = !(status === 3 || status === 4);

  return (
    <>
      <Box
        sx={{ display: "flex", flexDirection: "column", gap: 2, mt: 4, mx: 2 }}
      >
        {/* Quick Stats Section */}
        {!isProcessing && datasetInfo && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {/* Dataset quality score */}
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
              }}
            >
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                <Typography variant="h4">{dataset.name}</Typography>
              </Box>
              <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                <Tooltip
                  title={t("datasets:label.dataQualityScoreTooltip")}
                  arrow
                >
                  <Alert
                    severity={
                      datasetInfo?.quality_info?.data_quality_score >= 80
                        ? "success"
                        : datasetInfo?.quality_info?.data_quality_score >= 50
                          ? "warning"
                          : datasetInfo?.quality_info?.data_quality_score
                            ? "error"
                            : "info"
                    }
                    sx={{
                      fontSize: "1rem",
                      height: "45px",
                      display: "flex",
                      alignItems: "center",
                      p: "0 12px",
                    }}
                  >
                    {t("datasets:label.qualityScore", {
                      value:
                        datasetInfo?.quality_info?.data_quality_score != null
                          ? datasetInfo.quality_info.data_quality_score.toFixed(
                              2,
                            )
                          : t("common:na"),
                      unit:
                        datasetInfo?.quality_info?.data_quality_score != null
                          ? "%"
                          : "",
                    })}
                  </Alert>
                </Tooltip>
              </Box>
            </Box>
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                mb: 2,
                flexWrap: "wrap",
              }}
            >
              <Box
                sx={{
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "center",
                }}
              >
                <Typography variant="subtitle1" color="text.secondary">
                  {formatDate(dataset.created)}
                </Typography>
              </Box>

              {/* Buttons */}
              <Box
                sx={{
                  display: "flex",
                  alignItems: "flex-end",
                  gap: 4,
                  flexDirection: "column",
                }}
              >
                <Grid
                  sx={{
                    minHeight: "40px",
                    display: "flex",
                    gap: 4,
                    flexWrap: "wrap",
                    justifyContent: "flex-start",
                  }}
                >
                  <Button
                    variant="contained"
                    endIcon={<AddIcon />}
                    disabled={isProcessing}
                    className="new-notebook-button"
                    {...(tourContextType === "datasets"
                      ? { "data-tour": "datasets-new-notebook-button" }
                      : {})}
                    onClick={(e) => {
                      e.stopPropagation();
                      if (onNewItem) {
                        onNewItem();
                      }
                      if (tourContext && tourContext.run) {
                        const waitForNoteBox = (attempts = 0) => {
                          const noteBox =
                            document.querySelector(".notebook-note-box");
                          if (noteBox) {
                            setTimeout(() => {
                              if (
                                tourContext &&
                                typeof tourContext.nextStep === "function"
                              ) {
                                tourContext.nextStep();
                              }
                            }, 300);
                          } else if (attempts < 50) {
                            setTimeout(() => waitForNoteBox(attempts + 1), 100);
                          } else {
                            if (
                              tourContext &&
                              typeof tourContext.nextStep === "function"
                            ) {
                              tourContext.nextStep();
                            }
                          }
                        };
                        waitForNoteBox();
                      }
                    }}
                    sx={{ height: "40px" }}
                  >
                    {newItemButtonText}
                  </Button>
                </Grid>
              </Box>
            </Box>
            <Header
              totalRows={datasetInfo?.total_rows}
              totalColumns={datasetInfo?.total_columns}
              fileSize={datasetInfo?.general_info?.memory_usage_mb}
            />
            {/* Compute-metadata missing notice */}
            {!datasetInfo?.general_info && (
              <Box>
                <Alert severity="info" sx={{ mb: 2 }}>
                  {t("datasets:computeMetadata.missingNotice")}
                </Alert>
              </Box>
            )}
            {/* Data Quality Alerts */}
            <Box>
              <QualityAlerts
                key={dataset?.id}
                qualityInfo={datasetInfo?.quality_info}
                generalInfo={datasetInfo?.general_info}
                missingValues={datasetInfo?.nan}
                onNavigateTab={setTab}
              />
            </Box>
            {/* Tabs */}
            <PillTabs
              minHeight="48px"
              value={tab}
              onChange={(_, newValue) => setTab(newValue)}
            >
              <Tab label={t("datasets:label.overview")} />
              <Tab
                label={t("datasets:label.numericalAnalysis")}
                disabled={
                  !datasetInfo?.numeric_stats ||
                  Object.keys(datasetInfo.numeric_stats).length === 0
                }
              />
              <Tab
                label={t("datasets:label.categorical")}
                disabled={
                  !datasetInfo?.categorical_stats ||
                  Object.keys(datasetInfo.categorical_stats).length === 0
                }
              />
              <Tab
                label={t("datasets:label.text")}
                disabled={
                  !datasetInfo?.text_stats ||
                  Object.keys(datasetInfo.text_stats).length === 0
                }
              />
              <Tab
                label={t("datasets:label.dataQuality")}
                disabled={!datasetInfo?.quality_info}
              />
              <Tab
                label={t("datasets:label.correlations")}
                disabled={
                  !datasetInfo?.correlations ||
                  Object.keys(datasetInfo.correlations).length === 0
                }
              />
            </PillTabs>

            {/* Divider */}
            <Divider sx={{ my: 4 }} />

            {/* Content based on selected tab */}
            {tab === 0 && (
              <OverviewTab
                dataset={dataset}
                dtypes={datasetInfo?.general_info?.dtypes}
                columnTypes={columnTypes}
                nan={datasetInfo?.nan}
                total_rows={datasetInfo?.total_rows}
                onEditColumnName={updateDatasetInfo}
                fetchDatasetPage={fetchDatasetPage}
              />
            )}
            {tab === 1 && (
              <NumericTab
                numericStats={datasetInfo?.numeric_stats}
                scrollToColumn={scrollToColumn}
                setScrollToColumn={setScrollToColumn}
              />
            )}
            {tab === 2 && (
              <CategoricalTab
                categoricalStats={datasetInfo?.categorical_stats}
              />
            )}
            {tab === 3 && (
              <TextTab
                textStats={datasetInfo?.text_stats}
                scrollToColumn={scrollToColumn}
                setScrollToColumn={setScrollToColumn}
              />
            )}
            {tab === 4 && (
              <QualityTab
                qualityInfo={datasetInfo?.quality_info}
                totalRows={datasetInfo?.total_rows}
              />
            )}
            {tab === 5 && (
              <CorrelationsTab correlations={datasetInfo?.correlations} />
            )}
          </Box>
        )}

        {/* Processing placeholder */}
        {isProcessing && (
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              minHeight: 200,
              flexDirection: "column",
              gap: 4,
            }}
          >
            <CircularProgress color="primary" />
            <Typography>{t("datasets:label.processingTitle")}</Typography>
            <Typography
              variant="body2"
              color="text.secondary"
              textAlign="center"
            >
              {t("datasets:label.processingMessage")}
            </Typography>
          </Box>
        )}
      </Box>
    </>
  );
}
