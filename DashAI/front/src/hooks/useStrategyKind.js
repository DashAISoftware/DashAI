import { useEffect, useState } from "react";
import { getComponents } from "../api/component";

/**
 * How each evaluation strategy divides the dataset, once fetched.
 *
 * Strategy names never change for a given session, so the answer is cached
 * across components: several screens ask the same question about the same
 * session and none of them should trigger its own request.
 */
const kindCache = new Map();

/**
 * Read the split shape of the strategy a session uses.
 *
 * Screens used to ask this by comparing the stored strategy name against a
 * literal, which meant every new strategy silently read as "not cross
 * validation" and rendered the wrong controls. The backend reports the shape,
 * so it is read rather than guessed.
 *
 * @param {string|null} strategyName a session's evaluation_strategy
 * @returns {string|null} "holdout", "cv", or null while unknown
 */
export function useStrategyKind(strategyName) {
  const [kind, setKind] = useState(() => kindCache.get(strategyName) ?? null);

  useEffect(() => {
    if (!strategyName) {
      setKind(null);
      return undefined;
    }

    if (kindCache.has(strategyName)) {
      setKind(kindCache.get(strategyName));
      return undefined;
    }

    let cancelled = false;
    const fetchKind = async () => {
      try {
        const component = await getComponents({ model: strategyName });
        const value = component?.metadata?.kind ?? null;
        kindCache.set(strategyName, value);
        if (!cancelled) setKind(value);
      } catch (error) {
        console.error(`Error fetching the ${strategyName} metadata`, error);
        if (!cancelled) setKind(null);
      }
    };

    fetchKind();
    return () => {
      cancelled = true;
    };
  }, [strategyName]);

  return kind;
}

export default useStrategyKind;
