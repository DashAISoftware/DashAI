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
import { getConvertersOutputSlots } from "../../../api/modelSession";
import { validateConverter } from "../../notebooks/tool/toolValidation";
import { useExplorersAndConverters } from "../../notebooks/context/ExplorersAndConvertersContext";
import FormSessionConverterSection from "./FormSessionConverterSection";
import { buildAtomList } from "./buildAtomList";

/**
 * Converters-only sidebar for the session wizard's preprocessing step,
 * styled like the notebook's RightBar converters tab. Relies on the
 * notebook's own ExplorersAndConvertersProvider, mounted once at the
 * Models page level (see pages/models/ModelsContent.jsx) rather than
 * locally here — it must be the *same* instance the center panel's drop
 * target (PreprocessingStep) uses, or dragging a converter card onto the
 * center panel would never reach this sidebar's ToolList/pendingDropTool
 * resolution.
 */
export default function SessionConvertersRightBar({
  session,
  rawColumnTypes,
  onConvertersChanged,
  isApplying,
}) {
  const theme = useTheme();
  const { t } = useTranslation(["models", "datasets", "common"]);
  const { enqueueSnackbar } = useSnackbar();
  const { setColumnTypes } = useExplorersAndConverters();
  const [converters, setConverters] = useState([]);
  const [outputSlotsByConverterId, setOutputSlotsByConverterId] = useState({});
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState("list");

  // Seed the shared context's columnTypes so ConfigureToolModal's caption
  // reflects this session's raw dataset, not the empty default.
  useEffect(() => {
    setColumnTypes(rawColumnTypes || {});
  }, [rawColumnTypes, setColumnTypes]);

  useEffect(() => {
    let cancelled = false;
    getComponents({ selectTypes: ["Converter"] })
      .then((data) => {
        if (!cancelled) setConverters(data || []);
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

  // Real output slots for this session's own configured converters, each
  // instantiated with its own actual params (e.g. a `SimpleImputer`
  // configured with `add_indicator: true` really declares a second slot)
  // — unlike the generic tool metadata fetched above, which always
  // reflects a converter's *default* params and would never see that.
  useEffect(() => {
    let cancelled = false;
    if (!session?.converters?.length) {
      setOutputSlotsByConverterId({});
      return undefined;
    }
    getConvertersOutputSlots(session.converters)
      .then((data) => {
        if (!cancelled) setOutputSlotsByConverterId(data || {});
      })
      .catch((error) => {
        console.error("Failed to fetch converters' output slots:", error);
      });
    return () => {
      cancelled = true;
    };
  }, [session?.converters]);

  // Every raw dataset column is eligible scope here — same as the notebook
  // sidebar. Unlike the session flow's original design, output columns
  // aren't chosen yet at this point (that's a later wizard step), so
  // there's no "input vs output" distinction to filter by. `rawColumnTypes`
  // is the session's *raw* dataset column types — converters are no longer
  // applied immediately, so there's no preprocessed-columns state to read
  // here anymore (see Task 10 for where this prop is sourced from now).
  const datasetColumns = useMemo(
    () =>
      Object.entries(rawColumnTypes || {}).map(
        ([columnName, typeInfo], idx) => ({
          id: idx,
          columnName,
          valueType: typeInfo.type || t("common:unknown"),
          dataType: typeInfo.dtype || t("common:unknown"),
          order: idx,
        }),
      ),
    [rawColumnTypes, t],
  );

  // `session.converters` entries carry only what the backend persists
  // (id/converter/params/input_scope/target_column — see
  // `SessionConverterParams`), never `output_slots`, so those come from
  // the real-params fetch above, keyed by each entry's own `id`, before
  // handing anything to `buildAtomList`, which reads
  // `converter.metadata.output_slots`.
  const sessionConvertersWithMetadata = useMemo(
    () =>
      (session?.converters || []).map((entry) => ({
        ...entry,
        metadata: { output_slots: outputSlotsByConverterId[entry.id] || [] },
      })),
    [session?.converters, outputSlotsByConverterId],
  );

  const atoms = useMemo(
    () =>
      buildAtomList({
        datasetColumnTypes: rawColumnTypes,
        converters: sessionConvertersWithMetadata,
      }),
    [rawColumnTypes, sessionConvertersWithMetadata],
  );

  const validatedConverters = useMemo(
    () =>
      converters.map((converter) => {
        const validation = validateConverter(converter, datasetColumns, t);
        return {
          ...converter,
          // While a previous apply is still in flight, gray out every card
          // so the user can't fire a second overlapping PUT before the
          // first one's poll settles.
          disabled: isApplying || validation.disabled,
          tooltip: isApplying
            ? t("models:label.converterApplying")
            : validation.tooltip,
          validColumns: validation.validColumns,
        };
      }),
    [converters, datasetColumns, t, isApplying],
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
  // box below) so ConfigureToolModal never remounts FormSessionConverterSection
  // — and loses in-progress scope/parameter input — while it's open.
  const SessionFormSection = useMemo(() => {
    function Wrapped(sectionProps) {
      return (
        <FormSessionConverterSection
          {...sectionProps}
          atoms={atoms}
          session={session}
          onApplied={onConvertersChanged}
          onApplyError={onConvertersChanged}
        />
      );
    }
    return Wrapped;
  }, [atoms, session, onConvertersChanged]);

  // No outer SideBar/header here: this renders inside ModelsRightBar's
  // "Configure Session" wrapper (see ModelsRightBar.jsx), which is
  // deliberately bare — this component owns its own p:4 on every row
  // below, exactly like the notebook's RightBar does, so dividers reach
  // the panel's real edges instead of stopping short at some ancestor's
  // padding.
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
      {isApplying && (
        <Box
          sx={{
            px: 4,
            py: 1.5,
            bgcolor: theme.palette.ui.box,
            borderBottom: `1px solid ${theme.palette.ui.border}`,
            flexShrink: 0,
          }}
        >
          <Typography variant="caption" sx={{ color: "text.secondary" }}>
            {t("models:label.converterApplying")}
          </Typography>
        </Box>
      )}
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
              notebook={{ file_path: session?.dataset?.file_path }}
              FormComponent={SessionFormSection}
            />
          </Box>
        );
      })()}
    </Box>
  );
}

SessionConvertersRightBar.propTypes = {
  session: PropTypes.object.isRequired,
  rawColumnTypes: PropTypes.object,
  onConvertersChanged: PropTypes.func.isRequired,
  isApplying: PropTypes.bool,
};
