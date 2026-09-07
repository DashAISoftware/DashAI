import { useState, useEffect, useCallback, useMemo, useRef } from "react";

import { getExplainers } from "../../../api/explainer";
import { getComponents } from "../../../api/component";
import { getPredictions } from "../../../api/predict";
import { getModelSessionById } from "../../../api/modelSession";
import { getDatasetSample } from "../../../api/datasets";
import {
  EMPTY_EXPLAINER_ENTRY,
  explainerCacheKey,
  mergeExplainers,
} from "../../explainers/explainerCache";

/**
 * Owns everything data related for a run's results: the explainer and
 * prediction lists, their fetching/polling, the per card plot cache, the
 * shared explainer display names, the training dataset sample used by the
 * prediction cards, and the "a new explainer just appeared" signal that drives
 * the scroll-and-flash in the explainer tab. Keeping it here leaves RunResults
 * and the tab components purely about layout.
 */
export default function useRunResultsData({
  run,
  session,
  onRefresh,
  explainerRefreshTrigger,
}) {
  const runId = run.id;

  const [globalExplainers, setGlobalExplainers] = useState([]);
  const [localExplainers, setLocalExplainers] = useState([]);
  const [predictions, setPredictions] = useState([]);

  const [trainingDatasetSample, setTrainingDatasetSample] = useState(null);
  const [outputColumn, setOutputColumn] = useState(null);
  const [modelSessionDetail, setModelSessionDetail] = useState(null);

  // "global" | "local", which explainer scope is shown.
  const [explainerFilter, setExplainerFilter] = useState("global");
  // A just added explainer: newExplainerKey triggers the scroll and flash;
  // highlightedExplainerKey drives the ring animation.
  const [newExplainerKey, setNewExplainerKey] = useState(null);
  const [highlightedExplainerKey, setHighlightedExplainerKey] = useState(null);
  // Last measured height per card key, so placeholders reserve exact space.
  const cardHeightsRef = useRef({});
  // Explainer keys seen on the previous fetch; null until the first load so
  // the initial batch is not treated as newly added.
  const seenExplainerKeysRef = useRef(null);
  // Explainer component name to display name, fetched once and shared so cards
  // do not each fetch it (a per card fetch shifted heights).
  const [explainerDisplayNames, setExplainerDisplayNames] = useState({});
  // Per card plot state (items, edits, selection), so the list can unmount
  // offscreen cards without refetching or losing edits.
  const [explainerCache, setExplainerCache] = useState({});

  const getCacheEntry = useCallback(
    (key) => explainerCache[key] ?? EMPTY_EXPLAINER_ENTRY,
    [explainerCache],
  );
  const updateCacheEntry = useCallback((key, patch) => {
    setExplainerCache((prev) => ({
      ...prev,
      [key]: { ...(prev[key] ?? EMPTY_EXPLAINER_ENTRY), ...patch },
    }));
  }, []);

  // "Prediction #N" counts only this run's own predictions, numbered per
  // section (Dataset vs Manual) in creation order, not `prediction.id`, which
  // is a database wide key shared across every run and session.
  const predictionDisplayNumbers = useMemo(() => {
    const numbers = new Map();
    [
      predictions.filter((p) => p.dataset_id),
      predictions.filter((p) => !p.dataset_id),
    ].forEach((group) => {
      [...group]
        .sort((a, b) => a.id - b.id)
        .forEach((p, index) => numbers.set(p.id, index + 1));
    });
    return numbers;
  }, [predictions]);

  // includePredictions lets the running explainer poll refetch only the
  // explainers: predictions do not change during that window (their own
  // completion is tracked by job polling), so refetching them every 3s just
  // re renders the prediction cards for nothing.
  const fetchOperations = useCallback(
    async ({ includePredictions = true } = {}) => {
      if (!runId) return;

      try {
        const [globalExpls, localExpls, preds] = await Promise.all([
          getExplainers(runId, "global").catch(() => []),
          getExplainers(runId, "local").catch(() => []),
          includePredictions
            ? getPredictions(runId).catch(() => [])
            : Promise.resolve(null),
        ]);

        // Detect explainers added since the last fetch. First fetch seeds the
        // baseline; later fetches switch the scope toggle to the new explainer.
        const currentKeys = new Set([
          ...globalExpls.map((e) => `global-${e.id}`),
          ...localExpls.map((e) => `local-${e.id}`),
        ]);
        if (seenExplainerKeysRef.current === null) {
          seenExplainerKeysRef.current = currentKeys;
        } else {
          const added = [...currentKeys].filter(
            (key) => !seenExplainerKeysRef.current.has(key),
          );
          seenExplainerKeysRef.current = currentKeys;
          if (added.length > 0) {
            const key = added[added.length - 1];
            setExplainerFilter(key.startsWith("global-") ? "global" : "local");
            setNewExplainerKey(key);
          }
        }

        setGlobalExplainers((prev) => mergeExplainers(prev, globalExpls));
        setLocalExplainers((prev) => mergeExplainers(prev, localExpls));
        if (preds !== null) setPredictions(preds);

        // Drop cached state for explainers that no longer exist (deleted on
        // retrain), so the cache cannot grow or serve a stale entry.
        const validKeys = new Set([
          ...globalExpls.map((e) => explainerCacheKey("global", e)),
          ...localExpls.map((e) => explainerCacheKey("local", e)),
        ]);
        setExplainerCache((prev) => {
          const next = {};
          let removed = false;
          Object.keys(prev).forEach((key) => {
            if (validKeys.has(key)) next[key] = prev[key];
            else removed = true;
          });
          return removed ? next : prev;
        });
      } catch (error) {
        console.error("Error fetching operations:", error);
      }
    },
    [runId],
  );

  useEffect(() => {
    fetchOperations();
  }, [fetchOperations, explainerRefreshTrigger]);

  // Fetch explainer display names once and share them with every card.
  useEffect(() => {
    getComponents({ selectTypes: ["GlobalExplainer", "LocalExplainer"] })
      .then((components) => {
        const names = {};
        components.forEach((component) => {
          names[component.name] = component.display_name || component.name;
        });
        setExplainerDisplayNames(names);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    const sessionId = run.model_session_id || session?.id;
    if (!sessionId) return;
    let cancelled = false;
    getModelSessionById(sessionId)
      .then((sessionData) => {
        if (cancelled) return null;
        setModelSessionDetail(sessionData);
        setOutputColumn(sessionData.output_columns?.[0] ?? null);
        return getDatasetSample(sessionData.dataset_id);
      })
      .then((sample) => {
        if (!cancelled && sample) setTrainingDatasetSample(sample);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [run.model_session_id, session?.id]);

  // Refetch when run parameters change (after editing). Skip the first run:
  // the mount fetch is already covered by the effect above, so firing here on
  // mount too would double every initial request.
  const paramsChangedFirstRun = useRef(true);
  useEffect(() => {
    if (paramsChangedFirstRun.current) {
      paramsChangedFirstRun.current = false;
      return;
    }
    fetchOperations();
  }, [
    run.parameters,
    run.optimizer_parameters,
    run.goal_metric,
    fetchOperations,
  ]);

  const hasRunningExplainers =
    globalExplainers.some((e) => e.status === 1 || e.status === 2) ||
    localExplainers.some((e) => e.status === 1 || e.status === 2);

  useEffect(() => {
    if (!hasRunningExplainers) return;
    const interval = setInterval(
      () => fetchOperations({ includePredictions: false }),
      3000,
    );
    return () => clearInterval(interval);
  }, [hasRunningExplainers, fetchOperations]);

  // Clear the highlight after the animation, in its own effect so setting
  // newExplainerKey(null) elsewhere cannot cancel this timer (else the card
  // stays flagged and the ring replays on every remount, e.g. tab switch).
  useEffect(() => {
    if (!highlightedExplainerKey) return undefined;
    const timer = setTimeout(() => setHighlightedExplainerKey(null), 4000);
    return () => clearTimeout(timer);
  }, [highlightedExplainerKey]);

  // Explainers shown under the current scope toggle (global / local).
  const activeExplainers =
    explainerFilter === "global" ? globalExplainers : localExplainers;

  const handlePredictionCreated = useCallback(
    (prediction) => {
      if (prediction) {
        setPredictions((prev) => {
          const index = prev.findIndex((p) => p.id === prediction.id);
          if (index === -1) return [prediction, ...prev];
          const updated = [...prev];
          updated[index] = prediction;
          return updated;
        });
      } else {
        fetchOperations();
      }
      if (onRefresh) onRefresh();
    },
    [fetchOperations, onRefresh],
  );

  // Stable so memoized cards keep their identity across RunResults renders
  // (e.g. the 3s poll) instead of rerendering and restarting Plotly.
  const handleExplainerDeleted = useCallback(() => {
    fetchOperations();
    if (onRefresh) onRefresh();
  }, [fetchOperations, onRefresh]);

  const handlePredictionDeleted = useCallback(() => {
    fetchOperations();
    if (onRefresh) onRefresh();
  }, [fetchOperations, onRefresh]);

  return {
    globalExplainers,
    localExplainers,
    predictions,
    activeExplainers,
    explainerFilter,
    setExplainerFilter,
    newExplainerKey,
    setNewExplainerKey,
    highlightedExplainerKey,
    setHighlightedExplainerKey,
    explainerDisplayNames,
    cardHeightsRef,
    getCacheEntry,
    updateCacheEntry,
    hasRunningExplainers,
    predictionDisplayNumbers,
    outputColumn,
    modelSessionDetail,
    trainingDatasetSample,
    fetchOperations,
    handlePredictionCreated,
    handleExplainerDeleted,
    handlePredictionDeleted,
  };
}
