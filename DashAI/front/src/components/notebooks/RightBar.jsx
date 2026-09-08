import { useState, useEffect, useMemo } from "react";
import SideBar from "../threeSectionLayout/panelContainers/SideBar";
import { evaluateColumnEligibility } from "../../utils/columnEligibility";
import {
  Box,
  Typography,
  Tabs,
  Tab,
  ToggleButtonGroup,
  ToggleButton,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { ViewList, ViewModule } from "@mui/icons-material";
import AnalyticsIcon from "@mui/icons-material/Analytics";
import TransformIcon from "@mui/icons-material/Transform";
import SearchBar from "../threeSectionLayout/SearchBar";
import DescriptionPanel from "./DescriptionPanel";
import ToolList from "./tool/ToolList";
import ToolGrid from "./tool/ToolGrid";
import FormExplorerSection from "./explorerCreation/FormExplorerSection";
import FormConverterSection from "./converterCreation/FormConverterSection";
import { getComponents } from "../../api/component";
import { useSnackbar } from "notistack";
import { useTourContext } from "../tour/TourProvider";
import { useExplorersAndConverters } from "./context/ExplorersAndConvertersContext";
import { useTranslation } from "react-i18next";
import { useDatasetsAndNotebooks } from "../custom/contexts/DatasetsAndNotebooksContext";
import ColumnInsights from "./dataset/ColumnInsights";

function SectionHeader({ icon: Icon, label, count, mt, theme, t }) {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 2,
        mb: 3,
        mt: mt ?? 0,
        pb: 1,
        borderBottom: "1px solid",
        borderColor: theme.palette.divider,
      }}
    >
      <Icon sx={{ fontSize: 18, color: theme.palette.accent.main }} />
      <Typography
        variant="subtitle2"
        sx={{ flex: 1, color: "text.primary", fontWeight: 600 }}
      >
        {label}
      </Typography>
      <Typography variant="caption" sx={{ color: "text.secondary" }}>
        {t("datasets:label.toolsCount", { count })}
      </Typography>
    </Box>
  );
}

function RightBarDatasetView() {
  const { t } = useTranslation(["datasets"]);
  const { datasetInfo } = useDatasetsAndNotebooks();

  if (!datasetInfo) {
    return (
      <Box
        sx={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          p: 4,
        }}
      >
        <Typography
          variant="body2"
          sx={{ color: "text.secondary", textAlign: "center" }}
        >
          {t("datasets:label.selectNotebookToAccessAnalysisTools")}
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ flex: 1, overflowY: "auto" }}>
      <ColumnInsights
        numericStats={datasetInfo?.numeric_stats}
        textStats={datasetInfo?.text_stats}
      />
    </Box>
  );
}

export default function RightBar({ notebook, onToggle }) {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [converters, setConverters] = useState([]);
  const [explorers, setExplorers] = useState([]);
  const tourContext = useTourContext();
  const [viewMode, setViewMode] = useState("list");
  const { enqueueSnackbar } = useSnackbar();
  const { explorersAndConverters, columnTypes } = useExplorersAndConverters();
  const { t } = useTranslation(["datasets", "common"]);

  const datasetColumns = useMemo(
    () =>
      Object.entries(columnTypes).map(([columnName, typeInfo], idx) => ({
        id: idx,
        columnName,
        valueType: typeInfo.type || t("common:unknown"),
        dataType: typeInfo.dtype || t("common:unknown"),
        order: idx,
      })),
    [columnTypes, t],
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await getComponents({
          selectTypes: ["Converter", "Explorer"],
        });
        if (cancelled) return;
        setConverters(data.filter((item) => item.type === "Converter"));
        setExplorers(data.filter((item) => item.type === "Explorer"));
      } catch (error) {
        enqueueSnackbar(t("datasets:error.fetchingExplorersConverters"), {
          variant: "error",
        });
        console.error("Failed to fetch explorers/converters:", error);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [t]);

  // Clear search when the selected notebook changes
  useEffect(() => {
    setSearchQuery("");
  }, [notebook?.id]);

  // Validate explorers based on dataset columns
  const validateExplorer = (explorer) => {
    if (!datasetColumns.length) return { disabled: false, tooltip: "" };

    // The metadata contract lives in one place now: this used to be one of four
    // hand-written copies, and the copy in the exploration wizard had gone stale
    // on both the blacklist key and the empty-list polarity.
    const { validColumns, shortfall, restrictions, restricted } =
      evaluateColumnEligibility(explorer?.metadata, datasetColumns, {
        unknownLabel: t("common:unknown"),
      });

    let disabled = shortfall !== null;
    let tooltip =
      explorer.description || explorer.metadata?.short_description || "";

    if (shortfall !== null) {
      if (validColumns.length === 0) {
        tooltip += `\n\n${t("datasets:error.noValidColumnsForExplorer")}`;
      }
      const key =
        shortfall.kind === "exact"
          ? "datasets:error.requiresExactColumns"
          : "datasets:error.requiresMinColumns";
      tooltip += `\n\n${t(key, {
        required: shortfall.required,
        available: shortfall.available,
        count: shortfall.required,
      })}`;
    }

    // No column survived a restriction the component declared, which is a
    // different message from "this component needs more columns than exist".
    if (validColumns.length === 0 && restricted && restrictions.length > 0) {
      disabled = true;
      tooltip += `\n\n${t("datasets:error.noValidColumnsWithDtypesMentioned", {
        dtypes: restrictions.join(", "),
      })}`;
    }

    return { disabled, tooltip, validColumns };
  };

  // Validate converters based on dataset columns
  const validateConverter = (converter) => {
    if (!datasetColumns.length) return { disabled: false, tooltip: "" };

    // Same shared contract as the explorers. This copy never applied the
    // dtype blacklist at all, and SMOTE and SMOTEENN both declare one
    // (they refuse string, bool and unnamed dtypes), so the picker offered
    // them for datasets whose columns the backend would then reject.
    const { validColumns, shortfall, restrictions, restricted } =
      evaluateColumnEligibility(converter?.metadata, datasetColumns, {
        unknownLabel: t("common:unknown"),
      });

    let disabled = shortfall !== null;
    let tooltip =
      converter.description || converter.metadata?.short_description || "";

    if (shortfall !== null) {
      const key =
        shortfall.kind === "exact"
          ? "datasets:error.requiresExactColumns"
          : "datasets:error.requiresMinColumns";
      tooltip += `\n\n${t(key, {
        required: shortfall.required,
        available: shortfall.available,
        count: shortfall.required,
      })}`;
    }

    if (validColumns.length === 0 && restricted && restrictions.length > 0) {
      disabled = true;
      tooltip += `\n\n${t("datasets:error.noValidColumnsWithDtypesMentioned", {
        dtypes: restrictions.join(", "),
      })}`;
    }

    return { disabled, tooltip, validColumns };
  };

  const validatedExplorers = useMemo(
    () =>
      explorers.map((explorer) => {
        const validation = validateExplorer(explorer);
        return {
          ...explorer,
          disabled: validation.disabled,
          tooltip: validation.tooltip,
          validColumns: validation.validColumns,
          notebook,
        };
      }),
    [explorers, datasetColumns, notebook?.id],
  );

  const validatedConverters = useMemo(
    () =>
      converters.map((converter) => {
        const validation = validateConverter(converter);
        return {
          ...converter,
          disabled: validation.disabled,
          tooltip: validation.tooltip,
          validColumns: validation.validColumns,
          notebook,
        };
      }),
    [converters, datasetColumns, notebook?.id],
  );

  const { filteredExplorers, filteredConverters } = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    const tokens = query.split(/\s+/).filter(Boolean);

    const rankMatch = (item) => {
      const displayName = (
        item.metadata?.display_name ||
        item.name ||
        ""
      ).toLowerCase();
      const description = (
        item.metadata?.short_description ||
        item.description ||
        ""
      ).toLowerCase();
      if (tokens.every((token) => displayName.includes(token))) return 1;
      const combined = `${displayName} ${description}`;
      if (tokens.every((token) => combined.includes(token))) return 2;
      return 0;
    };

    const filterAndRank = (items) => {
      if (!tokens.length) return items;
      return items
        .map((item) => ({ item, rank: rankMatch(item) }))
        .filter(({ rank }) => rank > 0)
        .sort((a, b) => a.rank - b.rank)
        .map(({ item }) => item);
    };

    return {
      filteredExplorers: filterAndRank(validatedExplorers),
      filteredConverters: filterAndRank(validatedConverters),
    };
  }, [searchQuery, validatedExplorers, validatedConverters]);

  const handleChangeTab = (_event, newValue) => {
    setActiveTab(newValue);

    if (tourContext && tourContext.run) {
      setTimeout(() => {
        tourContext.nextStep();
      }, 500);
    }
  };

  return (
    <SideBar>
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          height: "100%",
          width: "100%",
        }}
        className="right-bar-container"
      >
        <Box
          sx={{
            p: 4,
            borderBottom: `1px solid ${theme.palette.ui.border}`,
            flexShrink: 0,
            height: 64,
            display: "flex",
            alignItems: "center",
            justifyContent: "flex-start",
          }}
        >
          <Typography variant="h6" color="text.primary">
            {t("datasets:label.analysisTools")}
          </Typography>
        </Box>

        {notebook ? (
          <>
            {/* Tabs Section */}
            <Tabs
              value={activeTab}
              onChange={handleChangeTab}
              centered
              sx={{ flexShrink: 0 }}
            >
              <Tab
                data-tour="explorers-tab"
                label={
                  <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                    <AnalyticsIcon sx={{ fontSize: 18 }} />
                    {t("datasets:label.explore")}
                  </Box>
                }
              />
              <Tab
                data-tour="converters-tab"
                label={
                  <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                    <TransformIcon sx={{ fontSize: 18 }} />
                    {t("datasets:label.convert")}
                  </Box>
                }
              />
            </Tabs>

            <Box
              sx={{
                flex: 1,
                display: "flex",
                flexDirection: "column",
                overflow: "hidden",
              }}
              className="explorer-converter-box"
            >
              {/* Search bar */}
              <Box
                sx={{
                  p: 4,
                  borderBottom: `1px solid ${theme.palette.ui.border}`,
                  flexShrink: 0,
                }}
              >
                <SearchBar
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onClear={() => setSearchQuery("")}
                  placeholder={t("datasets:label.searchExplorersConverters")}
                />
              </Box>
              {/* View Mode Toggle */}
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  px: 4,
                  py: 2,
                  borderBottom: `1px solid ${theme.palette.ui.border}`,
                  flexShrink: 0,
                }}
              >
                <Typography variant="caption" sx={{ color: "text.secondary" }}>
                  {t("datasets:label.viewMode")}
                </Typography>
                <ToggleButtonGroup
                  value={viewMode}
                  exclusive
                  onChange={(_, newMode) => newMode && setViewMode(newMode)}
                  size="small"
                  sx={{
                    "& .MuiToggleButton-root": {
                      color: "text.secondary",
                      border: "1px solid",
                      borderColor: theme.palette.ui.border,
                      "&.Mui-selected": {
                        bgcolor: theme.palette.ui.border,
                        color: theme.palette.accent.main,
                      },
                    },
                  }}
                >
                  <ToggleButton value="list">
                    <ViewList sx={{ fontSize: 18 }} />
                  </ToggleButton>
                  <ToggleButton value="grid">
                    <ViewModule sx={{ fontSize: 18 }} />
                  </ToggleButton>
                </ToggleButtonGroup>
              </Box>

              {/* Tool list and description */}
              <Box
                sx={{
                  display: "flex",
                  flexDirection: "column",
                  flex: 1,
                  overflow: "hidden",
                  minWidth: 0,
                }}
              >
                {/* Tool list - grid */}
                {(() => {
                  const isSearching = searchQuery.trim().length > 0;
                  const ListComponent =
                    viewMode === "list" ? ToolList : ToolGrid;
                  const containerSx =
                    viewMode === "list"
                      ? {
                          flex: 1,
                          overflowY: "auto",
                          overflowX: "hidden",
                          p: 4,
                          minWidth: 0,
                        }
                      : { flex: 1, overflow: "auto", p: 4 };

                  const hasExplorers = filteredExplorers.length > 0;
                  const hasConverters = filteredConverters.length > 0;

                  return (
                    <Box sx={containerSx}>
                      {isSearching ? (
                        <>
                          {hasExplorers && (
                            <>
                              <SectionHeader
                                icon={AnalyticsIcon}
                                label={t("datasets:label.explore")}
                                count={filteredExplorers.length}
                                theme={theme}
                                t={t}
                              />
                              <ListComponent
                                tools={filteredExplorers}
                                notebook={notebook}
                                FormComponent={FormExplorerSection}
                              />
                            </>
                          )}
                          {hasConverters && (
                            <>
                              <SectionHeader
                                icon={TransformIcon}
                                label={t("datasets:label.convert")}
                                count={filteredConverters.length}
                                mt={hasExplorers ? 6 : 0}
                                theme={theme}
                                t={t}
                              />
                              <ListComponent
                                tools={filteredConverters}
                                notebook={notebook}
                                FormComponent={FormConverterSection}
                              />
                            </>
                          )}
                          {!hasExplorers && !hasConverters && (
                            <Typography
                              variant="body2"
                              sx={{
                                color: "text.secondary",
                                textAlign: "center",
                                py: 4,
                              }}
                            >
                              {t("datasets:label.noToolsMatched")}
                            </Typography>
                          )}
                        </>
                      ) : activeTab === 0 ? (
                        <ListComponent
                          tools={filteredExplorers}
                          notebook={notebook}
                          FormComponent={FormExplorerSection}
                        />
                      ) : (
                        <ListComponent
                          tools={filteredConverters}
                          notebook={notebook}
                          FormComponent={FormConverterSection}
                        />
                      )}
                    </Box>
                  );
                })()}

                {/* Description panel - Fixed height */}
                <DescriptionPanel />
              </Box>
            </Box>
          </>
        ) : (
          <RightBarDatasetView />
        )}
      </Box>
    </SideBar>
  );
}
