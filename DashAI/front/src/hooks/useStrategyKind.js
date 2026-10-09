import { useEffect, useState } from "react";
import { getComponents } from "../api/component";

/**
 * What each evaluation strategy declares about itself, once fetched.
 *
 * Strategy names never change for a given session, so the answer is cached
 * across components: several screens ask the same question about the same
 * session and none of them should trigger its own request.
 */
const metadataCache = new Map();

/**
 * Read the metadata an evaluation strategy declares.
 *
 * Screens used to answer these questions by comparing the stored strategy
 * name against a literal, which meant every new strategy silently read as
 * "not cross validation" and rendered the wrong controls. The backend reports
 * what it does, so it is read rather than guessed.
 *
 * @param {string|null} strategyName a session's evaluation_strategy
 * @returns {object|null} the strategy metadata, or null while it is unknown
 */
export function useStrategyMetadata(strategyName) {
  const [metadata, setMetadata] = useState(
    () => metadataCache.get(strategyName) ?? null,
  );

  useEffect(() => {
    if (!strategyName) {
      setMetadata(null);
      return undefined;
    }

    if (metadataCache.has(strategyName)) {
      setMetadata(metadataCache.get(strategyName));
      return undefined;
    }

    let cancelled = false;
    const fetchMetadata = async () => {
      try {
        const component = await getComponents({ model: strategyName });
        const value = component?.metadata ?? {};
        metadataCache.set(strategyName, value);
        if (!cancelled) setMetadata(value);
      } catch (error) {
        console.error(`Error fetching the ${strategyName} metadata`, error);
        if (!cancelled) setMetadata({});
      }
    };

    fetchMetadata();
    return () => {
      cancelled = true;
    };
  }, [strategyName]);

  return metadata;
}

export function useStrategyKind(strategyName) {
  return useStrategyMetadata(strategyName)?.kind ?? null;
}

export default useStrategyKind;
