import { useState, useEffect, useRef } from "react";
import { getExplorerResults } from "../../../api/explorer";

/**
 * Hook to manage explorer results data
 * @param {Object} explorer The explorer whose results are fetched
 * @returns {Object} { loading, artifact, error, fetchExplorerResults }
 */
export function useExplorerResults(explorer) {
  const [loading, setLoading] = useState(false);
  const [artifact, setArtifact] = useState(null);
  const [error, setError] = useState(null);
  // Invalidates in-flight requests when the explorer changes or unmounts
  const requestIdRef = useRef(0);

  const fetchExplorerResults = async () => {
    // Only fetch if explorer exists and has finished status
    if (!explorer?.id || explorer.status !== 3) {
      return;
    }

    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;
    const isStale = () => requestId !== requestIdRef.current;

    setLoading(true);
    setError(null);
    try {
      const artifacts = await getExplorerResults(explorer.id);
      if (isStale()) return;

      const [firstArtifact] = artifacts ?? [];
      if (!firstArtifact?.type) {
        throw new Error("No artifacts in the response");
      }

      setArtifact(firstArtifact);
    } catch (err) {
      if (isStale()) return;
      // Results can disappear while the box is still mounted (explorer deleted,
      // result file removed): surface it as state instead of letting the
      // rejection escape the effect as an uncaught runtime error.
      console.error("Error fetching explorer results:", err);
      setArtifact(null);
      setError(err);
    } finally {
      if (!isStale()) {
        setLoading(false);
      }
    }
  };

  // Fetch the results data when explorer changes or status becomes "Finished"
  useEffect(() => {
    fetchExplorerResults();
    return () => {
      requestIdRef.current += 1;
    };
  }, [explorer?.id, explorer?.status]);

  return {
    loading,
    artifact,
    error,
    fetchExplorerResults,
  };
}
