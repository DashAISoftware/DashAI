import { useEffect, useRef, useState } from "react";
import { getPreprocessingStructure } from "../../../api/modelSession";

const DEBOUNCE_MS = 300;

/**
 * The estimated dataset structure along a session's preprocessing chain,
 * from the backend's infer_structure: the state after every step, their
 * errors and warnings, and the final state.
 *
 * Refetched on every change to the inputs, debounced so quick edits send
 * one request. Only the response to the latest inputs is kept: a slower
 * response to an earlier edit never overwrites a newer one.
 *
 * @param {object} args
 * @param {number} args.datasetId the session's dataset; nothing is fetched
 *   without one
 * @param {string[]} args.candidates original columns fed into the chain
 * @param {string[]} args.outputColumns the target columns
 * @param {Array<object>} args.steps the chain's `{converter, params, scope}`
 * @returns {{structure: object|null, loading: boolean, error: Error|null}}
 */
export default function usePreprocessingStructure({
  datasetId,
  candidates,
  outputColumns,
  steps,
}) {
  const [structure, setStructure] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const latestRequest = useRef(0);

  // A stable value to depend on: the caller may rebuild these arrays on
  // every render, and a step may carry extra UI-only fields.
  const payloadKey = JSON.stringify({
    datasetId,
    candidates: candidates || [],
    outputColumns: outputColumns || [],
    steps: (steps || []).map(({ converter, params, scope }) => ({
      converter,
      params,
      scope,
    })),
  });

  useEffect(() => {
    const payload = JSON.parse(payloadKey);
    const requestId = latestRequest.current + 1;
    latestRequest.current = requestId;
    if (!payload.datasetId) {
      setStructure(null);
      setLoading(false);
      return undefined;
    }
    setLoading(true);
    const timer = setTimeout(async () => {
      try {
        const result = await getPreprocessingStructure(payload);
        if (requestId === latestRequest.current) {
          setStructure(result);
          setError(null);
        }
      } catch (requestError) {
        if (requestId === latestRequest.current) {
          setError(requestError);
        }
      } finally {
        if (requestId === latestRequest.current) {
          setLoading(false);
        }
      }
    }, DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [payloadKey]);

  return { structure, loading, error };
}
