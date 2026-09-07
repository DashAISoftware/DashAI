import { React, useEffect, useState } from "react";
import { CircularProgress, Box } from "@mui/material";
import PropTypes from "prop-types";
import { useSnackbar } from "notistack";

import { getExplainerPlot as getExplainerPlotRequest } from "../../api/explainer";
import { useTranslation } from "react-i18next";
import ArtifactList from "../shared/ArtifactList";
import { patchArtifactPayload } from "../../utils/artifactOverrides";
import ExplainerInstanceTable from "./ExplainerInstanceTable";
import StoryBox from "./StoryBox";

/** Wrap legacy plotly JSON strings as plotly artifacts; pass typed dicts through. */
function parseExplanationArtifacts(items) {
  return items.map((item) =>
    typeof item === "string"
      ? { type: "plotly", payload: item, title: null, role: "explanation" }
      : item,
  );
}

export default function ExplainersPlot({
  explainer,
  scope,
  onSaveOverride = null,
  cacheEntry = null,
  onCacheUpdate = null,
}) {
  const { enqueueSnackbar } = useSnackbar();
  const cachedItems = cacheEntry ? cacheEntry.items : null;
  const [items, setItems] = useState(() => cachedItems ?? []);
  const [loading, setLoading] = useState(() => cachedItems == null);
  const { t } = useTranslation(["explainers"]);
  const isLocal = scope === "local";
  const datasetPath = isLocal ? explainer.input_dataset_path : null;

  const getExplainerPlot = async () => {
    setLoading(true);
    try {
      const response = await getExplainerPlotRequest(explainer.id, scope);
      if (!response || response.length === 0) {
        setItems([]);
        if (onCacheUpdate) onCacheUpdate({ items: [] });
        enqueueSnackbar(t("explainers:error.noData"), { variant: "warning" });
      } else {
        const parsed = parseExplanationArtifacts(response);
        setItems(parsed);
        if (onCacheUpdate) onCacheUpdate({ items: parsed });
      }
    } catch (error) {
      setItems([]);
      if (onCacheUpdate) onCacheUpdate({ items: [] });
      enqueueSnackbar(t("explainers:error.fetchExplainers"), {
        variant: "error",
      });
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (explainer.status !== 3) return;
    // Cache hit: reuse fetched artifacts, skip the network entirely so a card
    // scrolled back into view does not refetch.
    if (cacheEntry && cacheEntry.items != null) {
      setItems(cacheEntry.items);
      setLoading(false);
      return;
    }
    getExplainerPlot();
  }, [explainer.id, explainer.status, scope]);

  if (loading || explainer.status !== 3) {
    if (explainer.status === 4) {
      return <Box sx={{ p: 4 }}>{t("explainers:error.explainerFailed")}</Box>;
    }
    return (
      <Box sx={{ display: "flex", justifyContent: "flex-start", p: 2 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (items.length === 0) {
    return <Box sx={{ p: 2 }}>{t("explainers:error.noData")}</Box>;
  }

  // A grouped selector swaps which artifact sits in each slot, which drops the
  // viewer's local copy of an edit. Writing the saved figure back into the
  // fetched list means switching instance and back still shows it.
  const handleSaveOverride = onSaveOverride
    ? async (index, figure) => {
        await onSaveOverride(index, figure);
        const patched = patchArtifactPayload(
          items,
          index,
          JSON.stringify(figure),
        );
        setItems(patched);
        if (onCacheUpdate) onCacheUpdate({ items: patched });
      }
    : null;

  // Local explainers pass the explained rows dataset path so their grouped
  // selector shows the instance feature values instead of plain labels.
  return (
    <ArtifactList
      items={items}
      ctx={{ onSaveOverride: handleSaveOverride }}
      renderGroupSelector={(selectorProps) => (
        <ExplainerInstanceTable datasetPath={datasetPath} {...selectorProps} />
      )}
      wideSelector={Boolean(datasetPath)}
      renderStory={(entry) => (
        <StoryBox story={entry.story} groupTitle={entry.title} />
      )}
      fallbackGroupTitle={(index) =>
        t("explainers:label.instanceNumber", { number: index + 1 })
      }
      selection={
        onCacheUpdate
          ? {
              selectedFor: (index) => cacheEntry?.selectedGroups?.[index] ?? 0,
              onSelect: (index, value) =>
                onCacheUpdate({
                  selectedGroups: {
                    ...(cacheEntry?.selectedGroups ?? {}),
                    [index]: value,
                  },
                }),
            }
          : null
      }
    />
  );
}

ExplainersPlot.propTypes = {
  explainer: PropTypes.shape({
    id: PropTypes.number,
    status: PropTypes.number,
    input_dataset_path: PropTypes.string,
  }).isRequired,
  scope: PropTypes.string.isRequired,
  onSaveOverride: PropTypes.func,
  cacheEntry: PropTypes.shape({
    items: PropTypes.array,
    selectedGroups: PropTypes.object,
  }),
  onCacheUpdate: PropTypes.func,
};
