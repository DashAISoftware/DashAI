import { useState, useCallback, useEffect, useRef } from "react";
import { getComponents } from "../../api/component";

/**
 * Shared cache for the "Model"/"Metric" component lists, used across the
 * models module (session view, comparison table, available-models sidebar,
 * results graphs, ...). Without this, each consumer fetched the same list
 * independently, causing repeated identical requests whenever a session was
 * created/switched/updated.
 */
export function useModelComponents({ language }) {
  const [allModels, setAllModels] = useState([]);
  const [allMetrics, setAllMetrics] = useState([]);
  const [modelsByTask, setModelsByTask] = useState({});
  const pendingTaskFetches = useRef({});

  const fetchAllModels = useCallback(async () => {
    const response = await getComponents({ selectTypes: ["Model"] });
    setAllModels(response);
    return response;
  }, []);

  const fetchAllMetrics = useCallback(async () => {
    const response = await getComponents({ selectTypes: ["Metric"] });
    setAllMetrics(response);
    return response;
  }, []);

  // Component metadata (display_name, description) is translated server-side,
  // so cached entries go stale when the UI language changes.
  useEffect(() => {
    fetchAllModels();
    fetchAllMetrics();
    setModelsByTask({});
    pendingTaskFetches.current = {};
  }, [language, fetchAllModels, fetchAllMetrics]);

  const getModelsForTask = useCallback(
    (taskName) => {
      if (!taskName) return Promise.resolve([]);
      if (modelsByTask[taskName])
        return Promise.resolve(modelsByTask[taskName]);
      if (pendingTaskFetches.current[taskName]) {
        return pendingTaskFetches.current[taskName];
      }
      const promise = getComponents({
        selectTypes: ["Model"],
        relatedComponent: taskName,
      }).then((response) => {
        setModelsByTask((prev) => ({ ...prev, [taskName]: response }));
        delete pendingTaskFetches.current[taskName];
        return response;
      });
      pendingTaskFetches.current[taskName] = promise;
      return promise;
    },
    [modelsByTask],
  );

  return {
    allModels,
    fetchAllModels,
    allMetrics,
    fetchAllMetrics,
    getModelsForTask,
  };
}
