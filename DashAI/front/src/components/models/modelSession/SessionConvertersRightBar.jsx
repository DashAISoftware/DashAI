import { useEffect, useMemo, useState } from "react";
import PropTypes from "prop-types";
import {
  Box,
  Typography,
  ToggleButtonGroup,
  ToggleButton,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { ViewList, ViewModule } from "@mui/icons-material";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import SearchBar from "../../threeSectionLayout/SearchBar";
import ToolList from "../../notebooks/tool/ToolList";
import ToolGrid from "../../notebooks/tool/ToolGrid";
import { getComponents } from "../../../api/component";
import { evaluateColumnEligibility } from "../../../utils/columnEligibility";
import FormSessionConverterSection from "./FormSessionConverterSection";
import { buildColumnKeysAndTypes } from "./sessionColumnRefs";

/**
 * Converters-only sidebar for the session wizard's preprocessing step,
 * styled like the notebook module's own converters picker (same SearchBar,
 * ToolList/ToolGrid, category accordion, list/grid toggle). Unlike the
 * notebook flow, picking a converter here never fits anything or POSTs
 * anywhere — see FormSessionConverterSection, which just appends the
 * configured step to newExp.preprocessing.
 */
export default function SessionConvertersRightBar({
  newExp,
  setNewExp,
  dataset,
  datasetTypes,
}) {
  const theme = useTheme();
  const { t } = useTranslation(["models", "datasets", "common"]);
  const { enqueueSnackbar } = useSnackbar();
  const [converters, setConverters] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState("list");

  useEffect(() => {
    let cancelled = false;
    getComponents({ selectTypes: ["Converter"] })
      .then((data) => {
        if (!cancelled) setConverters(Array.isArray(data) ? data : []);
      })
      .catch((error) => {
        console.error("Failed to fetch converters:", error);
        enqueueSnackbar(t("datasets:error.fetchingConverters"), {
          variant: "error",
        });
      });
    return () => {
      cancelled = true;
    };
  }, [t]);

  // A new converter can be scoped on any raw dataset column OR the output
  // group (any declared slot) of any converter already configured — it
  // always lands at the end of the sequence, so every existing step is
  // "before" it and fair game to chain off. Gating this on raw columns
  // alone wrongly blocked, e.g., PCA on a text-only dataset (no raw
  // Integer/Float columns) even after adding Bag of Words, whose Integer
  // output group PCA could legitimately scope on.
  const { columnTypes: allColumnTypes } = useMemo(
    () =>
      buildColumnKeysAndTypes({
        datasetTypes,
        preprocessing: newExp.preprocessing,
      }),
    [datasetTypes, newExp.preprocessing],
  );

  const datasetColumns = useMemo(
    () =>
      Object.entries(allColumnTypes || {}).map(
        ([columnName, typeInfo], idx) => ({
          id: idx,
          columnName,
          valueType: typeInfo.type || t("common:unknown"),
          dataType: typeInfo.dtype || t("common:unknown"),
          order: idx,
        }),
      ),
    [allColumnTypes, t],
  );

  const validateConverter = (converter) => {
    if (!datasetColumns.length) return { disabled: false, tooltip: "" };

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

  const validatedConverters = useMemo(
    () =>
      converters.map((converter) => {
        const validation = validateConverter(converter);
        return { ...converter, ...validation };
      }),
    [converters, datasetColumns, t],
  );

  const filteredConverters = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return validatedConverters;
    const tokens = query.split(/\s+/).filter(Boolean);
    return validatedConverters.filter((item) => {
      const displayName = (item.display_name || item.name || "").toLowerCase();
      return tokens.every((token) => displayName.includes(token));
    });
  }, [searchQuery, validatedConverters]);

  // Stable identity across re-renders (e.g. every keystroke in the search
  // box) so ConfigureToolModal never remounts FormSessionConverterSection
  // — and loses in-progress scope/parameter input — while it's open.
  const SessionFormSection = useMemo(() => {
    function Wrapped(sectionProps) {
      return (
        <FormSessionConverterSection
          {...sectionProps}
          newExp={newExp}
          setNewExp={setNewExp}
          datasetTypes={datasetTypes}
          filePath={dataset?.file_path}
        />
      );
    }
    return Wrapped;
  }, [newExp, setNewExp, datasetTypes, dataset]);

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        height: "100%",
        width: "100%",
      }}
    >
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
          placeholder={t("datasets:label.searchConverters")}
        />
      </Box>
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
        >
          <ToggleButton value="list">
            <ViewList sx={{ fontSize: 18 }} />
          </ToggleButton>
          <ToggleButton value="grid">
            <ViewModule sx={{ fontSize: 18 }} />
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>
      {(() => {
        const ListComponent = viewMode === "list" ? ToolList : ToolGrid;
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
        return (
          <Box sx={containerSx}>
            <ListComponent
              tools={filteredConverters}
              notebook={{ file_path: dataset?.file_path }}
              FormComponent={SessionFormSection}
            />
          </Box>
        );
      })()}
    </Box>
  );
}

SessionConvertersRightBar.propTypes = {
  newExp: PropTypes.object.isRequired,
  setNewExp: PropTypes.func.isRequired,
  dataset: PropTypes.object,
  datasetTypes: PropTypes.object,
};
