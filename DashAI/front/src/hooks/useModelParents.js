import { useCallback, useEffect, useState } from "react";
import { getComponents } from "../api/component";

/*
 * This hook is used to get the parent models of a model
 * @param {string} parent - The parent model
 */

export default function useModelParents({ parent }) {
  const [models, setModels] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const getModels = async () => {
      try {
        setLoading(true);
        const result = await getComponents({
          componentParent: parent,
        });

        setModels(result);
      } catch (error) {
      } finally {
        setLoading(false);
      }
    };

    if (parent) {
      getModels();
    }
  }, [parent]);

  // Flip a single model's downloaded flag in place so an inline download/delete
  // is reflected in the cached list. Without this, switching models and coming
  // back would re-mount the download control from the stale (not-downloaded)
  // flag and show the Download button again.
  const markDownloaded = useCallback((name, isDownloaded) => {
    setModels((prev) =>
      prev
        ? prev.map((model) =>
            model.name === name
              ? { ...model, downloaded: isDownloaded }
              : model,
          )
        : prev,
    );
  }, []);

  return { models, loading, markDownloaded };
}
